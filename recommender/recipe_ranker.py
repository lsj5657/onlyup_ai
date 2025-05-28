def rank_recipes(user_ingredients, recipe_list, weight_similarity=0.4, weight_overlap=0.6):
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    model = SentenceTransformer("jhgan/ko-sbert-nli")
    user_input = ", ".join(user_ingredients)
    user_embedding = model.encode(user_input)

    recipe_names = [r["name"] for r in recipe_list]
    recipe_embeddings = model.encode(recipe_names)

    similarities = cosine_similarity([user_embedding], recipe_embeddings)[0]

    results = []
    for idx, recipe in enumerate(recipe_list):
        recipe_ingredients = [x.strip() for x in recipe["ingredients"].split(",")]
        common_count = len(set(user_ingredients) & set(recipe_ingredients))
        overlap = common_count / len(recipe_ingredients)
        sim_score = similarities[idx]
        final_score = weight_similarity * sim_score + weight_overlap * overlap

        results.append({
            "name": recipe["name"],
            "final_score": round(float(final_score), 3)  
        })


    return sorted(results, key=lambda x: x["final_score"], reverse=True)
