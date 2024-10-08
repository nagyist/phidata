# VertexAI Gemini Cookbook

> Note: Fork and clone this repository if needed

## Prerequisites

1. [Install](https://cloud.google.com/sdk/docs/install) the Google Cloud SDK
2. [Create a Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
3. [Enable the AI Platform API](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com)
4. [Authenticate](https://cloud.google.com/sdk/docs/initializing) with Google Cloud

```shell
gcloud auth application-default login
```


### 1. Create and activate a virtual environment

```shell
python3 -m venv ~/.venvs/aienv
source ~/.venvs/aienv/bin/activate
```

### 2. Export your Environment Variables

```shell
export PROJECT_ID=your-project-id
export LOCATION=us-central1
```

### 3. Install libraries

```shell
pip install -U google-cloud-aiplatform duckduckgo-search duckdb yfinance phidata
```

### 4. Run Agent without Tools

- Streaming on

```shell
python cookbook/providers/vertexai/basic_stream.py
```

- Streaming off

```shell
python cookbook/providers/vertexai/basic.py
```

### 5. Run Agent with Tools

- Yahoo Finance with streaming on

```shell
python cookbook/providers/vertexai/agent_stream.py
```

- Yahoo Finance without streaming

```shell
python cookbook/providers/vertexai/agent.py
```

- Finance Agent

```shell
python cookbook/providers/vertexai/finance_agent.py
```

- Data Analyst

```shell
python cookbook/providers/vertexai/data_analyst.py
```

- DuckDuckGo Search
```shell
python cookbook/providers/vertexai/web_search.py
```

### 6. Run Agent that returns structured output

```shell
python cookbook/providers/vertexai/structured_output.py
```

