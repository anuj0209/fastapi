from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import torch
import os
from typing import List

MODEL_PATH = "/models/model.pt"

app = FastAPI()
model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        model = torch.load(MODEL_PATH, map_location=device)
        model.to(device)
        model.eval()


class PredictRequest(BaseModel):
    input: List[float]


@app.get("/health")
def health():
    return {"status": "ok", "device": str(device)}


@app.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        content = await file.read()
        f.write(content)
    # Try loading
    try:
        load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")
    return {"status": "uploaded"}


@app.post("/predict")
def predict(req: PredictRequest):
    if model is None:
        # attempt to load if file exists
        if os.path.exists(MODEL_PATH):
            try:
                load_model()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")
        else:
            raise HTTPException(status_code=404, detail="Model not available. Upload first.")

    try:
        import numpy as np
        tensor = torch.tensor(req.input, dtype=torch.float32, device=device)
        # Ensure batch dimension
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        with torch.no_grad():
            out = model(tensor)
        # Convert output to list
        if isinstance(out, torch.Tensor):
            result = out.cpu().numpy().tolist()
        else:
            # handle tuple/list outputs
            result = []
            for o in out:
                if isinstance(o, torch.Tensor):
                    result.append(o.cpu().numpy().tolist())
                else:
                    result.append(o)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
