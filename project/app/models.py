from django.db import models
from pgvector.django import VectorField, CosineDistance
import http.client
import json


class Item(models.Model):
    name = models.CharField(max_length=255)
    embedding = VectorField(dimensions=768, editable=False, null=True)

    def __str__(self):
        return self.name

    def get_embedding_ollama(self, text: str):
        try:
            conn = http.client.HTTPConnection("localhost", 11434)
            payload = json.dumps({"model": "nomic-embed-text", "input": text})
            headers = {
                "Content-Type": "application/json",
            }
            conn.request("POST", "/api/embed", body=payload, headers=headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            result = json.loads(data)
            conn.close()
            return result["embeddings"][0]
        except Exception as e:
            raise Exception(f"Error generating embedding from Ollama: {e}")

    def save(self, *args, **kwargs):
        text = self.name
        self.embedding = self.get_embedding_ollama(text)
        super().save(*args, **kwargs)

    @staticmethod
    def search_by_embedding(search_term: str):
        try:
            search_embedding = Item().get_embedding_ollama(search_term)
            vector_value = search_embedding
            results = (
                Item.objects.annotate(
                    similarity=CosineDistance("embedding", vector_value)
                )
                .filter(similarity__lte=0.5)
                .order_by("similarity")
            )
            return results
        except Exception as e:
            print(f"Error searching by embedding: {e}")
            return Item.objects.none()
