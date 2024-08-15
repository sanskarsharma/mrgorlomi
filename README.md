# Mr Gorlomi

### Running on local
```bash
echo "OPENAI_API_KEY=<your-openai-key>" > .env  # replace value with your openai key
pip install -r requirements.txt
streamlit run streamlit_app.py --server.port=80 --server.address=0.0.0.0
```
