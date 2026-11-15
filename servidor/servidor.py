#!/usr/bin/env python3
"""Servidor do robo-cores3-lite, opção B: ouve, pensa e fala, tudo nesta máquina.

  python3 servidor/servidor.py

Um turno: WAV do robô → trava de silêncio → Whisper residente (inemavox) → claude -p pela assinatura, sem
ferramentas (com a foto, se veio) → voz residente (Chatterbox) → WAV 16 kHz mono 16 bits de volta.
Só biblioteca padrão. Só chama serviços em 127.0.0.1. Protocolo: DEFINICAO.md, seção 11.
"""
import base64
import hmac
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
import wave
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from inemavox import Inemavox  # noqa: E402

LIMITE_FALA = 1_000_000
LIMITE_FOTO = 200_000
DURACAO_MIN = 0.5
DURACAO_MAX = 15.5


def ler_env(caminho):
    cfg = {}
    if caminho.exists():
        for linha in caminho.read_text().splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                cfg[k.strip()] = os.path.expanduser(v.strip())
    return cfg


CFG = {
    "ROBO_PORTA": "8770",
    "ROBO_TOKEN": "",
    "INEMAVOX_URL": "http://127.0.0.1:8010",
    "WHISPER_DAEMON_URL": "http://127.0.0.1:7871",
    "VOZ_URL": "http://127.0.0.1:7872",
    "WHISPER_MODELO": "large-v3",
    "VOZ_REF": os.path.expanduser("~/projetos/timesmkt3/media/voice-refs/rachel.wav"),
    "CLAUDE_MODELO": "haiku",
    "HISTORICO_TURNOS": "6",
    "FOTO_VALIDADE": "60",
    "SILENCIO_DB": "-50",
    "CONDA_PY": os.path.expanduser("~/miniconda3/envs/chatterbox/bin/python3"),
}
CFG.update(ler_env(AQUI / ".env"))
for chave in ("INEMAVOX_URL", "WHISPER_DAEMON_URL", "VOZ_URL"):
    if not CFG[chave].startswith("http://127.0.0.1:"):
        raise SystemExit(f"{chave} tem de ser http://127.0.0.1:<porta> (o servidor só fala com esta máquina)")
if len(CFG["ROBO_TOKEN"]) < 16 or CFG["ROBO_TOKEN"].startswith("troque"):
    raise SystemExit("ROBO_TOKEN em servidor/.env: defina um texto longo (16+ caracteres)")

DADOS = AQUI / "dados"
VAZIO = DADOS / "vazio"
for p in (DADOS / "turnos", VAZIO):
    p.mkdir(parents=True, exist_ok=True)

TURNO = threading.Lock()   # um turno por vez: a GPU é uma só
FOTOS = {}                 # turno -> (instante, caminho)
FOTOS_TRAVA = threading.Lock()
INEMAVOX = Inemavox(CFG["INEMAVOX_URL"])


class Recusa(Exception):
    def __init__(self, codigo, erro, motivo=None):
        super().__init__(erro)
        self.codigo, self.erro, self.motivo = codigo, erro, motivo


def log(msg):
    print(f"{datetime.now():%H:%M:%S} {msg}", flush=True)


# ---------- serviços residentes (sobem sob demanda e saem sozinhos depois de 10 min parados) ----------

def _no_ar(url):
    try:
        urllib.request.urlopen(url + "/saude", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


def garantir(url, comando, nome, espera=120):
    if _no_ar(url):
        return 0.0
    t = time.time()
    log(f"subindo {nome}")
    with open(DADOS / f"{nome}.log", "ab") as saida:
        subprocess.Popen(comando, stdout=saida, stderr=subprocess.STDOUT, start_new_session=True)
    while time.time() - t < espera:
        if _no_ar(url):
            return time.time() - t
        time.sleep(1)
    raise Recusa(503, nome)


def garantir_whisper():
    porta = urllib.parse.urlparse(CFG["WHISPER_DAEMON_URL"]).port
    cmd = [CFG["CONDA_PY"], os.path.expanduser("~/projetos/inemavox/whisper_daemon.py"),
           "--porta", str(porta), "--modelo", CFG["WHISPER_MODELO"], "--ocioso", "600"]
    return garantir(CFG["WHISPER_DAEMON_URL"], cmd, "whisper")


def garantir_voz():
    porta = urllib.parse.urlparse(CFG["VOZ_URL"]).port
    cmd = [CFG["CONDA_PY"], str(AQUI / "voz_residente.py"), "--porta", str(porta), "--ocioso", "600"]
    return garantir(CFG["VOZ_URL"], cmd, "voz")


def _post_json(url, obj, timeout):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


# ---------- etapas ----------

def conferir_wav(dados):
    if dados[:4] != b"RIFF" or dados[8:12] != b"WAVE":
        raise Recusa(415, "formato")
    try:
        with wave.open(io.BytesIO(dados)) as w:
            taxa, canais, largura, quadros = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
    except wave.Error:
        raise Recusa(415, "formato")
    if (taxa, canais, largura) != (16000, 1, 2):
        raise Recusa(415, "formato")
    return quadros / taxa


def volume_medio(caminho):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(caminho), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=30)
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf)", r.stderr)
    return -999.0 if not m or m.group(1) == "-inf" else float(m.group(1))


def transcrever(wav):
    try:
        garantir_whisper()
        r = _post_json(CFG["WHISPER_DAEMON_URL"] + "/transcrever", {"audio": str(wav), "lang": "pt"}, 60)
        return " ".join(s.get("text", "").strip() for s in r.get("segments", [])).strip()
    except Recusa:
        raise
    except Exception as e:  # noqa: BLE001  — caminho lento, mas local: a fila do inemavox
        log(f"whisper residente falhou ({e}); usando a fila do inemavox")
        return INEMAVOX.transcrever(str(wav), CFG["WHISPER_MODELO"])


def historico(robo):
    arq = DADOS / f"conversa-{robo}.json"
    try:
        return json.loads(arq.read_text())
    except Exception:  # noqa: BLE001
        return []


def guardar_historico(robo, ouvido, resposta):
    arq = DADOS / f"conversa-{robo}.json"
    trocas = historico(robo) + [{"pessoa": ouvido, "robo": resposta, "quando": datetime.now().isoformat(timespec="seconds")}]
    arq.write_text(json.dumps(trocas[-50:], ensure_ascii=False, indent=1))


def pensar(robo, ouvido, foto):
    n = int(CFG["HISTORICO_TURNOS"])
    linhas = [f"Agora: {datetime.now():%d/%m/%Y %H:%M} (horário de Brasília)."]
    antes = historico(robo)[-n:]
    if antes:
        linhas.append("Conversa até aqui:")
        linhas += [f"Pessoa: {t['pessoa']}\nVocê: {t['robo']}" for t in antes]
    linhas.append(f"A pessoa disse agora: {ouvido}")
    conteudo = []
    if foto:
        conteudo.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                      "data": base64.b64encode(foto.read_bytes()).decode()}})
        linhas.append("(A imagem acima é o que a sua câmera está vendo agora.)")
    conteudo.append({"type": "text", "text": "\n".join(linhas)})
    entrada = json.dumps({"type": "user", "message": {"role": "user", "content": conteudo}}, ensure_ascii=False)

    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = ["claude", "-p", "--model", CFG["CLAUDE_MODELO"], "--tools", "", "--strict-mcp-config",
           "--no-session-persistence", "--input-format", "stream-json", "--output-format", "stream-json",
           "--verbose", "--system-prompt", (AQUI / "persona.txt").read_text()]
    r = subprocess.run(cmd, input=entrada, capture_output=True, text=True, cwd=VAZIO, env=env, timeout=90)
    for linha in r.stdout.splitlines():
        try:
            d = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "result":
            if d.get("is_error") or not (d.get("result") or "").strip():
                raise Recusa(500, "claude")
            return limpar_fala(d["result"])
    log(f"claude sem resultado: rc={r.returncode} {r.stderr[:200]}")
    raise Recusa(500, "claude")


def limpar_fala(texto):
    texto = re.sub(r"[*_#`>|~]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:600]


def falar(texto, pasta):
    garantir_voz()
    bruto = pasta / "resposta-24k.wav"
    r = _post_json(CFG["VOZ_URL"] + "/falar", {"texto": texto, "ref": CFG["VOZ_REF"], "saida": str(bruto), "lang": "pt"}, 120)
    if not r.get("ok"):
        raise Recusa(500, "voz")
    final = pasta / "resposta.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(bruto), "-ar", "16000", "-ac", "1",
                    "-c:a", "pcm_s16le", str(final)], check=True, timeout=60)
    return final


def turno(robo, dados, turno_foto):
    tempos = {}
    t0 = time.time()
    pasta = DADOS / "turnos" / f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"
    pasta.mkdir(parents=True)
    pergunta = pasta / "pergunta.wav"
    pergunta.write_bytes(dados)

    duracao = conferir_wav(dados)
    if duracao < DURACAO_MIN:
        raise Recusa(204, "curta", "curta")
    if duracao > DURACAO_MAX:
        raise Recusa(413, "grande")
    vol = volume_medio(pergunta)
    if vol < float(CFG["SILENCIO_DB"]):
        raise Recusa(204, "silencio", f"silencio ({vol:.1f} dB)")

    foto = None
    if turno_foto:
        with FOTOS_TRAVA:
            achado = FOTOS.pop(turno_foto, None)
        if achado and time.time() - achado[0] <= float(CFG["FOTO_VALIDADE"]):
            foto = pasta / "foto.jpg"
            foto.write_bytes(Path(achado[1]).read_bytes())

    with TURNO:
        t = time.time()
        ouvido = transcrever(pergunta)
        tempos["stt"] = time.time() - t
        if not re.search(r"\w", ouvido):
            raise Recusa(204, "vazio", "sem texto")
        t = time.time()
        resposta = pensar(robo, ouvido, foto)
        tempos["llm"] = time.time() - t
        t = time.time()
        wav = falar(resposta, pasta)
        tempos["tts"] = time.time() - t
    tempos["total"] = time.time() - t0
    guardar_historico(robo, ouvido, resposta)
    (pasta / "turno.json").write_text(json.dumps({"robo": robo, "ouvido": ouvido, "resposta": resposta,
                                                  "foto": bool(foto), "tempos": tempos}, ensure_ascii=False, indent=1))
    log(f"OUVIDO: {ouvido} | RESPOSTA: {resposta} | " + " ".join(f"{k}={v:.1f}" for k, v in tempos.items()))
    return ouvido, resposta, tempos, wav.read_bytes()


# ---------- HTTP ----------

class Robo(BaseHTTPRequestHandler):
    server_version = "robo-cores3-lite"
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _responder(self, codigo, corpo=b"", tipo="application/json", extras=None):
        self.send_response(codigo)
        if codigo != 204:
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
        for k, v in (extras or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if codigo != 204 and corpo:
            self.wfile.write(corpo)

    def _erro(self, codigo, erro, motivo=None):
        extras = {"X-Motivo": urllib.parse.quote(motivo)} if motivo else None
        if codigo == 204:
            self._responder(204, extras=extras)
        else:
            self._responder(codigo, json.dumps({"erro": erro}).encode(), extras=extras)

    def _corpo(self, limite):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > limite:
            # lê e descarta para não deixar o cliente pendurado
            restante = tamanho
            while restante > 0:
                bloco = self.rfile.read(min(65536, restante))
                if not bloco:
                    break
                restante -= len(bloco)
            raise Recusa(413, "grande")
        return self.rfile.read(tamanho)

    def _token_ok(self):
        return hmac.compare_digest(self.headers.get("X-Robo-Token", ""), CFG["ROBO_TOKEN"])

    def do_GET(self):
        if self.path == "/saude":
            return self._responder(200, b'{"ok": true}')
        self._erro(404, "rota")

    def do_POST(self):
        robo = re.sub(r"[^A-Za-z0-9_-]", "", self.headers.get("X-Robo-Id", "robo"))[:32] or "robo"
        try:
            if self.path not in ("/v1/fala", "/v1/foto"):
                raise Recusa(404, "rota")
            if not self._token_ok():
                self._corpo(LIMITE_FALA * 3)
                raise Recusa(401, "token")
            if self.path == "/v1/foto":
                dados = self._corpo(LIMITE_FOTO)
                if dados[:3] != b"\xff\xd8\xff":
                    raise Recusa(415, "formato")
                tid = uuid.uuid4().hex[:12]
                caminho = DADOS / f"foto-{tid}.jpg"
                caminho.write_bytes(dados)
                with FOTOS_TRAVA:
                    agora = time.time()
                    for k in [k for k, (t, _) in FOTOS.items() if agora - t > float(CFG["FOTO_VALIDADE"])]:
                        Path(FOTOS.pop(k)[1]).unlink(missing_ok=True)
                    FOTOS[tid] = (agora, str(caminho))
                return self._responder(200, json.dumps({"turno": tid}).encode())
            dados = self._corpo(LIMITE_FALA)
            ouvido, resposta, tempos, wav = turno(robo, dados, self.headers.get("X-Turno"))
            q = lambda s: urllib.parse.quote(s[:500])  # noqa: E731
            self._responder(200, wav, "audio/wav", {
                "X-Ouvido": q(ouvido), "X-Resposta": q(resposta),
                "X-Tempos": ";".join(f"{k}={v:.1f}" for k, v in tempos.items())})
        except Recusa as r:
            if r.codigo != 204:
                log(f"{self.path} {r.codigo} {r.erro}")
            self._erro(r.codigo, r.erro, r.motivo)
        except Exception as e:  # noqa: BLE001
            log(f"{self.path} 500 {type(e).__name__}: {e}")
            self._erro(500, "servidor")


def main():
    porta = int(CFG["ROBO_PORTA"])
    srv = ThreadingHTTPServer(("0.0.0.0", porta), Robo)
    log(f"robo-cores3-lite ouvindo na porta {porta} (voz: {Path(CFG['VOZ_REF']).stem}, modelo: {CFG['CLAUDE_MODELO']})")
    srv.serve_forever()


if __name__ == "__main__":
    main()
