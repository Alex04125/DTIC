import os
import pickle
import numpy as np
import json

# Path constants
MODEL_PATH = '/app/model.pkl'
INPUT_JSON_PATH = '/shared_data/vs/input.json'  # Adjust the path as needed
OUTPUT_JSON_PATH = '/shared_data/vs/output.json'  # Adjust the path as needed

# Load the trained model and scaler
def load_model(model_path):
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
            print("Model loaded successfully.")
        return model
    except FileNotFoundError:
        print("Model file not found.")
        return None

# Load input data from a JSON file
def load_input_data(json_path):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            input_data = np.array(data['features'])
            print("Input data loaded successfully.")
        return input_data
    except (FileNotFoundError, KeyError) as e:
        print(f"Error loading input data: {e}")
        return None

# Write output data to a JSON file
def write_output_data(output_json_path, predictions):
    try:
        with open(output_json_path, 'w') as f:
            json.dump({'predictions': predictions.tolist()}, f)
            print(f"Output data written to {output_json_path}.")
    except Exception as e:
        print(f"Error writing output data: {e}")

if __name__ == "__main__":
    # Load the trained model
    model = load_model(MODEL_PATH)
    if model is None:
        print("Unable to load the model.")
        exit(1)

    # Load the input data
    input_data = load_input_data(INPUT_JSON_PATH)
    if input_data is None:
        print("No valid input data found.")
        exit(1)
    print(input_data)
    print(model)
    # Perform inference directly with the raw features
    # model = model.fit(inpit)
    predictions = model.predict(input_data)

    # Write the output to JSON
    write_output_data(OUTPUT_JSON_PATH, predictions)
