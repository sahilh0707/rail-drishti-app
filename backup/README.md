# 🚂 Rail-Drishti: Intelligent Railway Assistance Platform

**Rail-Drishti** is a production-ready Streamlit application that provides AI-powered train delay predictions and intelligent railway assistance through an integrated chatbot.

## 🌟 Features

### 1. **Train Delay Predictor**
* ML-powered delay prediction using XGBoost
* Dynamic form inputs populated from real railway data
* Real-time predictions with confidence metrics
* Beautiful, responsive UI with visual indicators
* Support for all major Indian railway routes

### 2. **Railway Assistant Chatbot**
* RAG (Retrieval-Augmented Generation) powered responses
* Vector search integration for accurate information retrieval
* Conversational interface with chat history
* Context-aware responses about Indian Railways

## 📁 Project Structure

```
rail-drishti-app/
├── app.py                      # Main Streamlit application
├── api_client.py               # Backend integration (ML model + chatbot)
├── data/
│   └── indian_railway_data.csv # Railway dataset (100 records)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── QUICKSTART.txt              # Quick start guide
└── PROJECT_SUMMARY.md          # Detailed project documentation
```

## 🚀 Quick Start

### **Prerequisites**
* Python 3.8 or higher
* Databricks workspace (for backend integration)
* Gemini API key (for chatbot functionality)

### **Installation**

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   
   Edit `api_client.py` and update the following:
   ```python
   GEMINI_API_KEY = "your-gemini-api-key-here"
   ```

3. **Verify Data File**
   
   Ensure `data/indian_railway_data.csv` exists and contains railway data.

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

5. **Access the App**
   
   Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

## 🎯 Usage

### **Train Delay Predictor Page**

1. Select train details from the dropdowns:
   * Train ID
   * Train Number  
   * Source Station
   * Destination Station
   * Distance
   * Scheduled Arrival Time
   * Travel Date
   * Season
   * Run Frequency

2. Click **"🎯 Predict Delay"**

3. View prediction results with:
   * Predicted delay in minutes
   * Delay category (On Time / Delayed)
   * Delay duration in hours and minutes
   * Confidence level

### **Railway Assistant Page**

1. Type your railway-related query in the chat input
2. Get instant AI-powered responses
3. View source documents used for answers
4. Clear chat history with the "Clear Chat" button

## 🔧 Configuration

### **Databricks Configuration**

In `api_client.py`, configure your Databricks connection:

```python
CATALOG = "workspace"
SCHEMA = "default"
TABLE_NAME = "workspace.default.indian_railway_delay_data"
VECTOR_SEARCH_ENDPOINT = "railway_vs_endpoint"
VECTOR_INDEX_NAME = "workspace.default.railway_vector_index"
```

### **Model Configuration**

The delay prediction model uses:
* **Algorithm**: XGBoost Regressor
* **Estimators**: 100
* **Learning Rate**: 0.1
* **Features**: Train ID, route, distance, time, season, frequency

### **Chatbot Configuration**

The chatbot uses:
* **LLM**: Google Gemini Pro
* **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
* **Vector Search**: Databricks Vector Search
* **Top-K Retrieval**: 5 chunks

## 📊 Data Schema

The application uses the following data schema:

| Column | Type | Description |
|--------|------|-------------|
| Train_id | String | Unique train identifier |
| Train_name | String | Train name |
| Train_no | Integer | Train number |
| Source | String | Source station |
| Destitnation | String | Destination station |
| Date | String | Travel date |
| Distance(Km) | Integer | Distance in kilometers |
| Sc_arr__time | String | Scheduled arrival time |
| Act_arr_time | Timestamp | Actual arrival time |
| Dealy_min | String | Delay in minutes |
| Season | String | Season (Winter/Summer/Monsoon) |
| Run_frequency | String | Frequency (Daily/Weekly/Tri-Weekly) |

## 🎨 UI Features

* **Modern Design**: Clean, professional interface with custom CSS
* **Responsive Layout**: Wide layout for better data visibility
* **Interactive Elements**: Spinners, success messages, and error handling
* **Visual Metrics**: Color-coded delay indicators and metrics
* **Collapsible Sections**: Expandable input details view
* **Chat Interface**: Native Streamlit chat components

## 🔐 Security Notes

* Store API keys in environment variables (not hardcoded)
* Use `.gitignore` to exclude sensitive files
* Implement authentication for production deployments
* Validate all user inputs before processing

## 🚧 Troubleshooting

### **Common Issues**

**Issue**: Module not found errors
* **Solution**: Run `pip install -r requirements.txt`

**Issue**: Dataset not found error
* **Solution**: Verify `data/indian_railway_data.csv` exists

**Issue**: Prediction fails
* **Solution**: Ensure Databricks connection is configured and table exists

**Issue**: Chatbot not responding
* **Solution**: Verify Gemini API key is valid and Vector Search is set up

### **Debug Mode**

Enable Streamlit debug mode:
```bash
streamlit run app.py --logger.level=debug
```

## 📈 Performance Optimization

* **Caching**: Uses `@st.cache_data` for dataset loading
* **Lazy Loading**: Models loaded on-demand
* **Efficient Queries**: Optimized Spark DataFrame operations
* **Vector Search**: Fast similarity search for chatbot context

## 🛠️ Development

### **Local Development**

1. Make changes to `app.py` or `api_client.py`
2. Streamlit auto-reloads on file changes
3. Test thoroughly before deploying

### **Adding New Features**

* **New Predictors**: Add to `api_client.py` and create UI in `app.py`
* **UI Improvements**: Modify custom CSS in `app.py`
* **Data Sources**: Update `load_data()` function

## 📝 Backend Integration

### **Delay Predictor Backend**
Located at: `/Workspace/Users/mc240041016@iiti.ac.in/Drafts/delay predictor`

The prediction backend:
* Loads trained XGBoost model
* Processes input features
* Returns delay predictions with metadata

### **Chatbot Backend**
Located at: `/Workspace/Users/mc240041032@iiti.ac.in/chatbot`

The chatbot backend:
* Retrieves relevant documents using Vector Search
* Generates responses using Gemini Pro
* Maintains conversation context

## 📚 Additional Resources

* [Streamlit Documentation](https://docs.streamlit.io)
* [Databricks Documentation](https://docs.databricks.com)
* [XGBoost Documentation](https://xgboost.readthedocs.io)
* [Gemini API Documentation](https://ai.google.dev/docs)

## 🤝 Contributing

To contribute to this project:

1. Make your changes
2. Test thoroughly
3. Update documentation
4. Submit for review

## 📄 License

This project is intended for educational and demonstration purposes.

## 👥 Support

For issues or questions:
* Check the troubleshooting section
* Review Databricks logs
* Verify all configurations

---

**Built with ❤️ using Streamlit, Databricks, and Google Gemini**
