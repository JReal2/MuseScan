from ultralytics import YOLO

if __name__ == "__main__":
    # Load a model
    model = YOLO('yolo11m.pt')
    
    # Train the model
    model.train(
        data="head_dataset/data.yaml",
        epochs=200,
        imgsz=896,
        batch=16,
        name="yolo11n_with_note_cnn"
    )