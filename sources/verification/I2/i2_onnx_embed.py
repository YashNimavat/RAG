"""MiniLM-L6 via the ONNX export (chroma mirror): mean pooling, L2 normalise, max 256 WordPiece tokens."""
import numpy as np, onnxruntime as ort
from tokenizers import Tokenizer
class Embedder:
    def __init__(self, d):
        self.tok = Tokenizer.from_file(f"{d}/tokenizer.json")
        self.tok.enable_truncation(max_length=256); self.tok.enable_padding(pad_id=0, pad_token="[PAD]")
        self.sess = ort.InferenceSession(f"{d}/model.onnx", providers=["CPUExecutionProvider"])
        self.names = [i.name for i in self.sess.get_inputs()]
    def n_tokens(self, texts):
        t = Tokenizer.from_str(self.tok.to_str()); t.no_truncation(); t.no_padding()
        return [len(e.ids) for e in t.encode_batch(texts)]
    def encode(self, texts, bs=32):
        out = []
        for i in range(0, len(texts), bs):
            enc = self.tok.encode_batch(texts[i:i+bs])
            ids = np.array([e.ids for e in enc], dtype=np.int64); m = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": m, "token_type_ids": np.zeros_like(ids)}
            h = self.sess.run(None, {k: feed[k] for k in self.names})[0]
            v = (h * m[..., None]).sum(1) / m.sum(1, keepdims=True)
            out.append(v / np.linalg.norm(v, axis=1, keepdims=True))
        return np.vstack(out).astype(np.float32)
