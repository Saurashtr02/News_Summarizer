

from transformers import BartForConditionalGeneration, BartTokenizer
from datasets import load_dataset
from transformers import Trainer, TrainingArguments


model_name = 'facebook/bart-base' 
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)


dataset = load_dataset('cnn_dailymail', '3.0.0')

def tokenize_function(examples):
    model_inputs = tokenizer(examples['article'], max_length=1024, truncation=True)
    labels = tokenizer(examples['summary'], max_length=150, truncation=True)
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

dataset = dataset.map(tokenize_function, batched=True)


training_args = TrainingArguments(
    output_dir='./results', 
    num_train_epochs=1,  
    per_device_train_batch_size=2,  
    logging_dir='./logs',
    save_steps=1000,
    save_total_limit=2,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset['train'],
    eval_dataset=dataset['test'],  
)


trainer.train()


model.save_pretrained('./fine_tuned_bart')
tokenizer.save_pretrained('./fine_tuned_bart')
