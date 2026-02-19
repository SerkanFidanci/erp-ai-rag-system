"""
Fine-tuning Script - Unsloth ile QLoRA
Qwen2.5-coder modelini ERP SQL için eğitir

Gereksinimler:
- NVIDIA GPU (8GB+ VRAM önerilir)
- CUDA 11.8+
- Python 3.10+

Kurulum:
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps trl peft accelerate bitsandbytes
"""

import os
import json
import torch

def check_requirements():
    """Gereksinimleri kontrol et"""
    print("Gereksinimler kontrol ediliyor...")
    
    # CUDA
    if not torch.cuda.is_available():
        print("❌ CUDA bulunamadı! GPU gerekli.")
        print("   CPU ile eğitim çok yavaş olur.")
        return False
    
    print(f"✓ CUDA mevcut: {torch.cuda.get_device_name(0)}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Unsloth
    try:
        from unsloth import FastLanguageModel
        print("✓ Unsloth yüklü")
    except ImportError:
        print("❌ Unsloth yüklü değil!")
        print("   Kurulum: pip install unsloth")
        return False
    
    return True


def train_model():
    """Modeli eğit"""
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset
    
    print("\n" + "="*60)
    print("   ERP SQL Fine-tuning Başlıyor")
    print("="*60)
    
    # 1. Model yükle
    print("\n1. Model yükleniyor...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",  # 4-bit quantized
        max_seq_length=2048,
        dtype=None,  # Auto detect
        load_in_4bit=True,
    )
    
    # 2. LoRA adapter ekle
    print("2. LoRA adapter ekleniyor...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    
    # 3. Veri yükle
    print("3. Eğitim verisi yükleniyor...")
    dataset = load_dataset('json', data_files='training_data/train.jsonl', split='train')
    print(f"   {len(dataset)} örnek yüklendi")
    
    # 4. Prompt formatı
    def formatting_prompts_func(examples):
        texts = []
        for msgs in examples['messages']:
            text = tokenizer.apply_chat_template(msgs, tokenize=False)
            texts.append(text)
        return {"text": texts}
    
    dataset = dataset.map(formatting_prompts_func, batched=True)
    
    # 5. Trainer oluştur
    print("4. Trainer hazırlanıyor...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            num_train_epochs=3,  # 3 epoch genellikle yeterli
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=42,
            output_dir="outputs",
            save_strategy="epoch",
        ),
    )
    
    # 6. Eğit
    print("5. Eğitim başlıyor...")
    print("   Bu işlem GPU'nuza göre 10-60 dakika sürebilir.")
    print("-"*60)
    
    trainer_stats = trainer.train()
    
    print("-"*60)
    print(f"✓ Eğitim tamamlandı!")
    print(f"  Süre: {trainer_stats.metrics['train_runtime']:.1f} saniye")
    
    # 7. Kaydet
    print("\n6. Model kaydediliyor...")
    model.save_pretrained("erp-sql-model-lora")
    tokenizer.save_pretrained("erp-sql-model-lora")
    print("   LoRA adapter: erp-sql-model-lora/")
    
    return model, tokenizer


def export_to_gguf():
    """Modeli GGUF formatına çevir (Ollama için)"""
    from unsloth import FastLanguageModel
    
    print("\n" + "="*60)
    print("   GGUF Export (Ollama için)")
    print("="*60)
    
    # LoRA modelini yükle
    print("1. LoRA model yükleniyor...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="erp-sql-model-lora",
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    
    # GGUF'a çevir
    print("2. GGUF'a çevriliyor...")
    model.save_pretrained_gguf(
        "erp-sql-model-gguf",
        tokenizer,
        quantization_method="q4_k_m"  # 4-bit quantization
    )
    
    print("\n✓ GGUF dosyası oluşturuldu: erp-sql-model-gguf/")
    print("\nOllama'ya eklemek için:")
    print("  1. Modelfile oluştur")
    print("  2. ollama create erp-sql -f Modelfile")


def create_ollama_modelfile():
    """Ollama Modelfile oluştur"""
    modelfile = '''FROM ./erp-sql-model-gguf/unsloth.Q4_K_M.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""

SYSTEM """Sen bir MSSQL veritabanı uzmanısın. Kullanıcının Türkçe sorusunu SQL sorgusuna çeviriyorsun.
Kurallar:
- SADECE SQL yaz, açıklama yapma
- SELECT ile başla
- Firma adı için P.UNVAN kullan"""

PARAMETER temperature 0.1
PARAMETER num_predict 500
PARAMETER stop "<|im_end|>"
'''
    
    with open('Modelfile', 'w') as f:
        f.write(modelfile)
    
    print("✓ Modelfile oluşturuldu")
    print("\nKullanım:")
    print("  ollama create erp-sql -f Modelfile")
    print("  ollama run erp-sql")


def main():
    import sys
    
    print("="*60)
    print("   ERP SQL Fine-tuning Tool")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("""
Kullanım:
  python finetune.py check      - Gereksinimleri kontrol et
  python finetune.py train      - Modeli eğit
  python finetune.py export     - GGUF'a çevir
  python finetune.py modelfile  - Ollama Modelfile oluştur
  python finetune.py all        - Hepsini yap
        """)
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'check':
        check_requirements()
    
    elif cmd == 'train':
        if check_requirements():
            train_model()
    
    elif cmd == 'export':
        export_to_gguf()
    
    elif cmd == 'modelfile':
        create_ollama_modelfile()
    
    elif cmd == 'all':
        if check_requirements():
            train_model()
            export_to_gguf()
            create_ollama_modelfile()
            print("\n" + "="*60)
            print("   Tüm işlemler tamamlandı!")
            print("="*60)
            print("\nSon adımlar:")
            print("  ollama create erp-sql -f Modelfile")
            print("  ollama run erp-sql 'bugün kaç sipariş var'")


if __name__ == '__main__':
    main()
