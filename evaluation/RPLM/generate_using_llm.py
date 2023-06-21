import sys
import pandas as pd
import galai as gal
from llama_cpp import Llama
import galai as gal
import pickle

model = None

def get_model(model_name):
    global model
    if model_name == 'llama':
        model = Llama(model_path="/home/singh_shruti/workspace/rep_learning/sci_qa/llama.cpp/models/llama/7B/ggml-model-q4_0.bin", n_ctx=5000)
    elif model_name == "galactica":
        model = gal.load_model("mini")
    else:
        raise NotImplementedError("Implemented models are llama and galactica.")
    return model

def generate_using_llm(ranking_prompt, model_name, model):
    if model_name == 'llama':
        output = model(ranking_prompt + " Answer:", max_tokens=2000, stop=["Question:"])
        return output['choices'][0]['text']
    elif model_name == 'galactica':
        return model.generate(ranking_prompt)
    else:
        raise NotImplementedError("Implemented models are llama and galactica.")

def generate_rankings(model_name, model):
    model_ans_list = []
    df = pd.read_excel('./prompt_data/PromptDataLLM.xlsx', sheet_name='GroundTruth')

    with pd.ExcelWriter(f'/prompt_data/{model_name}_RPG.xlsx') as writer:
        for _, row in enumerate(df.iterrows()):
            ranking_prompt = row[1]['Prompt']
            ranking_prompt = ranking_prompt.replace("  ", " ")
            ranking_prompt = ranking_prompt.replace("  ", " ")
            ans = generate_using_llm(ranking_prompt, model_name, model)

            ground_truth = row[1]['GT']
            ground_truth = ground_truth.replace("  ", " ")
            ground_truth = ground_truth.replace("  ", " ")
            local_dict = {'prompt': ranking_prompt, 'llm_answer': ans, 'GT': ground_truth}
            model_ans_list.append(local_dict)

            with open(f'./prompt_data/{model_name}_RPG.pkl', 'ab') as f:
                pickle.dump(local_dict, f)

        subdf = pd.DataFrame(model_ans_list)
        subdf.to_excel(writer, sheet_name=f'{model_name}')

if __name__ == "__main__":
    model_name = sys.argv[1]
    model = get_model(model_name)
    generate_rankings(model_name=model_name, model=model)