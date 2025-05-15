from ultralytics import YOLO

if __name__ == "__main__":
    # Load a model
    model = YOLO('yolo11x.pt')

    # Train the model
    model.train(
        data="dataset_split/data.yaml",
        epochs=200,
        imgsz=640,
        batch=16,
        name="yolo11x_with_note_cnn"
    )