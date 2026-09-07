from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PARAKH API")


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "PARAKH API is running"
    }


@app.post("/analyze")
async def analyze_product(file: UploadFile = File(...)):

    return {
        "status": "success",
        "filename": file.filename,
        "product": {
            "name": "Sample Packaged Product",
            "brand": "Sample Brand",
            "net_quantity": "500 g",
            "mrp": "₹120",
            "manufacturer": "Sample Manufacturer"
        },
        "compliance": {
            "status": "Pending",
            "score": 0
        }
    }