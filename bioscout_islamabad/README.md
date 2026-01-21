# BioScout Islamabad 🌿🦉

A biodiversity monitoring platform for Islamabad's natural areas.

BioScout allows users to report and track biodiversity observations using AI-assisted species identification. The platform leverages Retrieval-Augmented Generation (RAG) to provide intelligent responses to queries about local flora and fauna.

![BioScout Screenshot](static/images/samples/screenshot.png)

## Setup

1. Clone this repository
2. Run `./setup_dev.sh` to set up the development environment
3. Edit the `.env` file with your actual API keys
4. Install dependencies with `pip install -r requirements.txt`
5. Run the application with `python app.py`

## Features

- 📱 Record biodiversity observations with images
- 🔍 AI-assisted species identification
- 🌍 Interactive map visualization
- 💬 Natural language querying with RAG
- 📊 Detailed biodiversity data collection
- Animal and plant species identification using AI
- Observation recording and management
- Interactive map of observations
- Knowledge base of local flora and fauna

## Species Identification

BioScout Islamabad uses two methods for species identification:

1. **OpenAI API** - General AI-based identification
2. **iNaturalist API** - Specialized identification for plants and animals with taxonomic details

The iNaturalist integration provides:
- Accurate species identification with confidence scores
- Taxonomic classification (kingdom, family, genus, etc.)
- Conservation status information
- Additional details like habitat, behavior, and ecology (when available)

### Testing the iNaturalist API

You can test the iNaturalist integration by running:

```bash
python test_inaturalist.py
```

To identify a species from an image:

```bash
python test_inaturalist.py --image static/images/samples/leopard.jpg
```

## API Keys

This application requires the following API keys:

- **OpenAI API Key**: For general species identification using AI
- **iNaturalist API Token**: For specialized identification using the iNaturalist database

Add these keys to the `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
INATURALIST_API_TOKEN=your_inaturalist_api_token_here
```

To obtain an iNaturalist API token:
1. Create an account at [iNaturalist.org](https://www.inaturalist.org/)
2. Go to your account settings
3. Create an application to get your API token

## Data Sources

The application uses two main datasets:
- `animals_observations.csv`: Contains animal species observations
- `plants_observations.csv`: Contains plant species observations

Both datasets include species information, location data, and identification details for flora and fauna found in Islamabad's natural areas.

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key (for species identification and RAG)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bioscout-islamabad.git
   cd bioscout-islamabad
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### Running the Application

Start the Flask development server:

```bash
python app.py
```

The application will be available at [http://localhost:5001](http://localhost:5001).

## Architecture

BioScout Islamabad is built with the following components:

- **Flask:** Web framework for the backend API
- **Leaflet.js:** Interactive mapping library
- **OpenAI API:** For species identification and RAG
- **LlamaIndex:** For knowledge base management and retrieval

### Directory Structure

```
bioscout_islamabad/
├── data/                      # Data storage (CSV files, knowledge base)
├── models/                    # Data models
├── routes/                    # API routes
├── services/                  # Business logic services
├── static/                    # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                 # HTML templates
├── app.py                     # Application entry point
├── config.py                  # Configuration settings
└── fix_numpy.py               # Utility for fixing numpy compatibility
```

## Working with RAG System

The application uses a Retrieval-Augmented Generation (RAG) system to provide context-aware responses to user queries. The system combines two approaches:

1. **LlamaIndex Integration:** For advanced vector-based retrieval (requires compatible numpy)
2. **Simple RAG Fallback:** Basic keyword matching for systems with compatibility issues

To fix numpy compatibility issues, run:

```bash
python fix_numpy.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 