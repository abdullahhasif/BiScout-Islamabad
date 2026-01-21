#!/bin/bash

# Setup script for BioScout Islamabad development environment

echo "Setting up development environment for BioScout Islamabad..."

# Create .env file with sample API keys
echo "Creating .env file with sample API keys..."
cat > .env << EOL
# Environment variables for BioScout Islamabad
# Replace these with your actual API keys

# OpenAI API Key (required for species identification)
OPENAI_API_KEY=your_openai_api_key_here

# iNaturalist API Token (for enhanced species identification)
INATURALIST_API_TOKEN=your_inaturalist_api_token_here
EOL

echo ".env file created. Please edit it with your actual API keys."

# Create sample images directory
echo "Creating sample images directory..."
mkdir -p static/images/samples

# Download some sample images if curl is available
if command -v curl &> /dev/null; then
    echo "Downloading sample test images..."
    
    # Create a function to download images
    download_image() {
        local url=$1
        local filename=$2
        echo "Downloading $filename..."
        curl -s -o "static/images/samples/$filename" "$url"
    }
    
    # Sample URLs for testing - replace with actual URLs or comment out if not needed
    download_image "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Common_leopard.jpg/800px-Common_leopard.jpg" "leopard.jpg"
    download_image "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Indian-Muntjacs.jpg/800px-Indian-Muntjacs.jpg" "barking_deer.jpg"
    download_image "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/White-throated_Kingfisher_%28Halcyon_smyrnensis%29_Photograph_By_Shantanu_Kuveskar.jpg/800px-White-throated_Kingfisher_%28Halcyon_smyrnensis%29_Photograph_By_Shantanu_Kuveskar.jpg" "white_kingfisher.jpg"
    download_image "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Pinus_wallichiana_India4.jpg/800px-Pinus_wallichiana_India4.jpg" "pine_tree.jpg"
    download_image "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Cedrus_deodara_India2.jpg/800px-Cedrus_deodara_India2.jpg" "cedar.jpg"
    
    echo "Sample images downloaded successfully."
else
    echo "curl command not found. Please download sample images manually."
fi

# Create necessary directories if they don't exist
echo "Creating necessary directories..."
mkdir -p data/vector_db
mkdir -p data/knowledge_files

# Create a basic README file with usage information
echo "Creating README file..."
cat > README.md << EOL
# BioScout Islamabad

A biodiversity monitoring platform for Islamabad's natural areas.

## Setup

1. Clone this repository
2. Run \`./setup_dev.sh\` to set up the development environment
3. Edit the \`.env\` file with your actual API keys
4. Install dependencies with \`pip install -r requirements.txt\`
5. Run the application with \`python app.py\`

## Features

- Animal and plant species identification using AI
- Observation recording and management
- Interactive map of observations
- Knowledge base of local flora and fauna

## API Keys

This application requires the following API keys:

- OpenAI API Key: For species identification using AI
- iNaturalist API Token: For enhanced species identification using the iNaturalist database

Add these keys to the \`.env\` file in the project root.
EOL

echo "Setup complete! You can now edit the .env file with your actual API keys and run the application." 