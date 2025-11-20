# fine_tune_bart.py

from transformers import BartForConditionalGeneration, BartTokenizer
from datasets import load_dataset
from transformers import Trainer, TrainingArguments

# Load pretrained BART model and tokenizer
model_name = 'facebook/bart-base'  # Using the smaller BART model
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

# Load your dataset (CNN/Daily Mail or your custom dataset)
dataset = load_dataset('cnn_dailymail', '3.0.0')

def tokenize_function(examples):
    model_inputs = tokenizer(examples['article'], max_length=1024, truncation=True)
    labels = tokenizer(examples['summary'], max_length=150, truncation=True)
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

dataset = dataset.map(tokenize_function, batched=True)

# Set up training arguments
training_args = TrainingArguments(
    output_dir='./results',  # Save model checkpoints here
    num_train_epochs=1,  # You can increase epochs if you have more time
    per_device_train_batch_size=2,  # Adjust batch size to fit memory
    logging_dir='./logs',
    save_steps=1000,
    save_total_limit=2,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset['train'],
    eval_dataset=dataset['test'],  # Optional validation
)

# Fine-tune the model
trainer.train()

# Save the fine-tuned model
model.save_pretrained('./fine_tuned_bart')
tokenizer.save_pretrained('./fine_tuned_bart')
