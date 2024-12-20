import joblib
from sklearn.preprocessing import StandardScaler

def predict(CPU_Utilization, Memory_Usage, Bandwidth_Utilization,
            Throughput, Latency, Jitter, Packet_Loss, Error_Rates,
            Connection_Establishment_Termination_Times, Network_Availability,
            Transmission_Delay, Grid_Voltage, Cooling_Temperature,
            Network_Traffic_Volume):
    """
    Predict system status using the trained model
    Returns:
    0 - NORMAL
    1 - WARNING
    2 - CRITICAL
    """
    # Load the trained model and scaler
    model = joblib.load('Model.joblib')
    scaler = joblib.load('Scaler.joblib')

    # Create input array in the correct order
    input_features = [
        CPU_Utilization,
        Memory_Usage,
        Bandwidth_Utilization,
        Throughput,
        Latency,
        Jitter,
        Packet_Loss,
        Error_Rates,
        Connection_Establishment_Termination_Times,
        Network_Availability,
        Transmission_Delay,
        Grid_Voltage,
        Cooling_Temperature,
        Network_Traffic_Volume
    ]

    # Reshape and scale the input
    input_reshaped = [input_features]
    scaled_input = scaler.transform(input_reshaped)

    # Make prediction
    prediction = model.predict(scaled_input)
    
    return int(prediction[0])  # Ensure integer output (0, 1, or 2)