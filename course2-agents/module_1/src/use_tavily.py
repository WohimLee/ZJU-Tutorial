

# To install: pip install tavily-python
from tavily import TavilyClient
client = TavilyClient("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")
response = client.search(
    query="英伟达股价"
)
for item in response["results"]:
    print(item["url"])
    print(item["title"])
    print(item["content"])



pass