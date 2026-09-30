# AWS Student Fine-Tuning Guide for LISAN (Ethiopian Multilingual AI)

This guide walks you through fine-tuning **NLLB-200** on your 68,000+ curated Ethiopian translation dataset using your **AWS University Account**.

---

## 📁 Prepared Files in This Repository

We have already created and prepared everything for you:

1. **`data/training_data/train.jsonl`** (29.4 MB, 64,623 training pairs across all 5 languages)
2. **`data/training_data/val.jsonl`** (1.54 MB, 3,401 validation pairs)
3. **`notebooks/fine_tune_nllb_aws.ipynb`** (Interactive Jupyter Notebook ready for 1-click training)
4. **`scripts/train_nllb_lora.py`** (Standalone CLI training script for headless EC2 instances)

---

## 🚀 Option A: Amazon SageMaker Studio (Recommended & Easiest for University Accounts)

Most university AWS accounts (AWS Academy, Vocareum, or Canvas) come with **Amazon SageMaker Studio** enabled. It requires **zero command line or SSH setup**.

### Step 1: Open SageMaker Studio
1. Log into your university AWS Console.
2. In the top search bar, type **SageMaker** and click **Amazon SageMaker**.
3. In the left navigation menu, click **Studio** (or **Domains**).
4. Click **Open Studio** next to your user profile.

### Step 2: Upload Your Training Files
Once the SageMaker Studio (JupyterLab) interface opens:
1. In the left file explorer, click the **Upload Files** icon (upward arrow).
2. Upload these 3 files:
   - `notebooks/fine_tune_nllb_aws.ipynb`
   - `data/training_data/train.jsonl`
   - `data/training_data/val.jsonl`

### Step 3: Choose a GPU Kernel & Instance
1. Double-click `fine_tune_nllb_aws.ipynb` to open it.
2. In the top right of the notebook, click on the **Kernel / Image** selector.
3. Choose:
   - **Image**: `PyTorch 2.x (Python 3.10 GPU Optimized)` or `Data Science 3.0`
   - **Instance Type**: **`ml.g4dn.xlarge`** (NVIDIA T4 16GB VRAM, ~$0.52/hr) or **`ml.g5.xlarge`** (NVIDIA A10G 24GB VRAM)
4. Wait 1–2 minutes for the GPU container to warm up.

### Step 4: Run the Notebook
1. Click **Run → Run All Cells** (or run cell by cell using `Shift + Enter`).
2. Cell 2 will verify your GPU:
   ```
   ✓ Detected GPU: Tesla T4 (15.78 GB VRAM)
   ```
3. Training will run across the 64,623 bilingual pairs using 4-bit QLoRA.
4. Estimated training time: **~1.5 to 2.5 hours**.
5. Once completed, Cell 8 generates:
   ```
   lisan_nllb_lora.zip (~50 MB)
   ```
6. Right-click `lisan_nllb_lora.zip` in the file browser and click **Download** to save it to your laptop!

---

## ⚡ Option B: Amazon EC2 GPU Instance (`g4dn.xlarge`)

If your university account gives you direct EC2 permissions:

1. Go to **EC2 Console → Launch Instance**.
2. **Name**: `lisan-gpu-training`
3. **AMI**: Search for **Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.x (Ubuntu 22.04)**.
4. **Instance Type**: Select **`g4dn.xlarge`** (4 vCPUs, 16GB RAM, NVIDIA T4 16GB).
5. **Key Pair**: Select or create an SSH key pair (`.pem`).
6. **Storage**: Set disk size to **50 GiB** (gp3).
7. Click **Launch Instance**.

### Connect and Run:
```bash
# 1. SSH into the instance
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>

# 2. Activate PyTorch GPU environment
source activate pytorch

# 3. Clone or upload your project files
scp -i your-key.pem -r data/training_data scripts/train_nllb_lora.py ubuntu@<your-ec2-public-ip>:~/

# 4. Install training dependencies
pip install peft bitsandbytes datasets accelerate sacrebleu sentencepiece

# 5. Launch training in background (screen or tmux)
python train_nllb_lora.py \
    --train_file training_data/train.jsonl \
    --val_file training_data/val.jsonl \
    --output_dir ./lisan_nllb_lora_final \
    --batch_size 16 \
    --num_epochs 3
```

---

## 💡 Troubleshooting Common University AWS Account Quirks

### 1. "Vcpu limit exceeded" or "Instance type not available in region"
* **Cause**: Your account default GPU quota is 0 in the current region, or the university restricted certain regions.
* **Fix**: Check your AWS region in the top right corner. Ensure you are in **`us-east-1` (N. Virginia)** or **`us-west-2` (Oregon)** — these two regions have the highest GPU availability and lowest costs.
* **Alternative**: If your university account blocks GPU EC2 instances completely, you can upload `fine_tune_nllb_aws.ipynb` and `train.jsonl`/`val.jsonl` directly to **Google Colab** (free T4 GPU) or **Amazon SageMaker Studio Lab** ([studiolab.sagemaker.aws](https://studiolab.sagemaker.aws/)).

### 2. Don't Forget to Stop/Terminate When Done!
* Once you download `lisan_nllb_lora.zip`, make sure to **Shut Down** your SageMaker instance or **Terminate** your EC2 instance so you don't burn your student credits while idle.
