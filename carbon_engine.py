def calculate_carbon_credits(plant_count, sensor_data):
    """
    Calculate carbon credits based on plant count and sensor data.
    
    Args:
        plant_count (int): Number of detected plants.
        sensor_data (dict): Dictionary with sensor readings including 'temperature' and 'humidity'.
        
    Returns:
        dict: Calculation results including biomass, carbon content, CO2 credits, and consistency score.
    """
    # Calculate the total estimated biomass. Assume an average plant weight factor of 2.5 kg.
    total_biomass = plant_count * 2.5
    
    # Calculate the Carbon sequestered using standard forestry equation
    carbon_content = total_biomass * 0.5
    co2_credits = carbon_content * 3.67
    
    # Calculate a consistency_score (0-100).
    consistency_score = 100
    
    # Deduct points if temperature > 35°C or humidity < 40%.
    temperature = sensor_data.get("temperature", 25)
    humidity = sensor_data.get("humidity", 50)
    
    if temperature > 35:
        consistency_score -= 15
    
    if humidity < 40:
        consistency_score -= 15
        
    # Ensure the score does not drop below 0
    consistency_score = max(0, consistency_score)
        
    return {
        "total_biomass": total_biomass,
        "carbon_content": carbon_content,
        "co2_credits": co2_credits,
        "consistency_score": consistency_score
    }

if __name__ == "__main__":
    # Example usage
    sample_sensor_data = {
        "temperature": 36.5,  # Above 35 (Should deduct points)
        "humidity": 35.0,     # Below 40 (Should deduct points)
        "solar_radiation": 850
    }
    sample_plant_count = 120
    
    result = calculate_carbon_credits(sample_plant_count, sample_sensor_data)
    
    print("Carbon Credits Calculation Results:")
    for key, value in result.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
