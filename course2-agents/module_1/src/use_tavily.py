
import os

# To install: pip install tavily-python
from tavily import TavilyClient
client = TavilyClient(os.getenv("TAVILY_API_KEY"))
response = client.search(
    query="英伟达股价"
)
for item in response["results"]:
    print(item["url"])
    print(item["title"])
    print(item["content"])



pass