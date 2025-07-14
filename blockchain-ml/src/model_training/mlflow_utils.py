import mlflow

def setup_mlflow():
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("blockchain_model_training") 