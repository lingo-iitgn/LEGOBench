from vllm import LLM, SamplingParams
import argparse
import pandas as pd

model_name_map = {"meta-llama/Llama-2-7b-chat-hf": "llama2_7b_chat", "meta-llama/Llama-2-13b-chat-hf": "llama2_13b_chat", "meta-llama/Llama-2-7b-hf": "llama2_7b", "meta-llama/Llama-2-13b-hf": "llama2_13b", "mistralai/Mistral-7B-v0.1": "mistral_7b", "mistralai/Mistral-7B-Instruct-v0.1": "mistral_7b_instruct", "lmsys/vicuna-13b-v1.5": "vicuna_13b", "lmsys/vicuna-7b-v1.5": "vicuna_7b", "HuggingFaceH4/zephyr-7b-beta": "zephyr_7b_beta", "tiiuae/falcon-7b": "falcon_7b", "tiiuae/falcon-7b-instruct": "falcon_7b_instruct", "facebook/galactica-6.7b": "galactica_7b"}

def model_response_gen(model_name):
    if model_name in ["mistralai/Mistral-7B-v0.1", "mistralai/Mistral-7B-Instruct-v0.1", "tiiuae/falcon-7b", "tiiuae/falcon-7b-instruct", "HuggingFaceH4/zephyr-7b-beta"]:
        llm = LLM(model=model_name, tensor_parallel_size=1, dtype="half")
    else:
        llm = LLM(model=model_name, tensor_parallel_size=1)
    model_tokenizer = llm.get_tokenizer()
    model_max_len = llm.llm_engine.model_config.max_model_len
    clean_model_name = model_name_map[model_name]

    model_ans_list = []
    prompts_list = []
    df = pd.read_excel('./data/rplm.xlsx')
    for _, row in enumerate(df.iterrows()):
        ranking_prompt = row[1]['instruction'] + "\n" + row[1]['model_options']
        local_dict = {'prompt': ranking_prompt, 'GT': row[1]['GT']}
        model_ans_list.append(local_dict)
        if len(model_tokenizer.tokenize(ranking_prompt)) < model_max_len:
            prompts_list.append(ranking_prompt)
        else:
            tokens_list = model_tokenizer.tokenize(ranking_prompt)
            prompts_list.append(model_tokenizer.convert_tokens_to_string(tokens_list[:model_max_len-5]))
    
    sampling_params = SamplingParams(temperature=0.1, top_p=0.95, max_tokens=4096, stop=['Question:', '\n\n\n\n'])
    outputs = llm.generate(prompts_list, sampling_params)
    generated_rank_list = []
    for output in outputs:
        generated_rank_list.append(output.outputs[0].text)

    for _, ranks in enumerate(generated_rank_list):
        model_ans_list[_][f'{clean_model_name}_gen_rank'] = ranks

    df = pd.DataFrame(model_ans_list)
    df.to_excel(f'./data/llm_responses/{clean_model_name}.xlsx')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', choices=list(model_name_map.keys()), help='name of the model to use for generation, specifically the hf repo name')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    model_response_gen(args.model_name)