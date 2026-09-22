---
language:
- am
license: cc-by-4.0
library_name: transformers
pipeline_tag: automatic-speech-recognition
tags:
- amharic
- ethiopia
- speech-recognition
- ctc
- wav2vec2-bert
metrics:
- wer
- cer
base_model: badrex/Ethio-ASR-multilingual-600M
model-index:
- name: hohe-asr-amharic
  results:
  - task:
      type: automatic-speech-recognition
      name: Automatic Speech Recognition
    dataset:
      type: google/fleurs
      name: FLEURS am_et (test)
      config: am_et
      split: test
    metrics:
    - type: wer
      value: 0.1604
      name: WER (with the 5-gram)
    - type: cer
      value: 0.0599
      name: CER (with the 5-gram)
---

# ሆሄ ASR, Amharic speech to text

A hohe is a letter of the Ge'ez alphabet, the character itself. This model
turns Amharic speech into those letters, and it is the first of the Hohe
family.

Amharic speech in, Amharic text out. One pass over the audio, no word by word
generation, so it runs about five times faster than a Whisper of similar
accuracy and it does not invent sentences when nobody is speaking.

Trained on 880 hours of Amharic: read speech, five regional dialects,
broadcast and interview recordings, phone calls, and conversation from the
internet. It is meant for real audio, so it was trained through noise, rooms,
8 kHz phone lines and clips up to a minute long.

**16.1% word error and 5.4% character error** on our held
out test set, whose speakers appear nowhere in training.

## How to use it

```python
import soundfile as sf, torch
from transformers import AutoModelForCTC, AutoProcessor

proc = AutoProcessor.from_pretrained("snapwre/hohe-asr-amharic")
model = AutoModelForCTC.from_pretrained("snapwre/hohe-asr-amharic").eval()

audio, sr = sf.read("clip.wav")          # 16 kHz mono
x = proc(audio, sampling_rate=16000, return_tensors="pt")
with torch.inference_mode():
    logits = model(**x).logits
print(proc.batch_decode(logits.argmax(-1))[0])
```

### With the language model, which is what the numbers above are

The 5-gram that ships in `lm/` is worth about 14% of the word errors.
Its two weights were tuned on development data only, never on a test set, and
they are in `lm/decoder.json`.

```python
from pyctcdecode import build_ctcdecoder
import json

cfg = json.load(open("lm/decoder.json"))
vocab = proc.tokenizer.get_vocab()
labels = [""] * (max(vocab.values()) + 1)
for tok, i in vocab.items():
    labels[i] = " " if tok == "|" else ("" if i == proc.tokenizer.pad_token_id else tok)

decoder = build_ctcdecoder(labels, "lm/am-5gram.bin", alpha=cfg["alpha"], beta=cfg["beta"])
print(decoder.decode(logits[0].numpy()))
```

The model writes an `[AMH]` tag at the start of its output. Strip it.

## What it scores

Character and word error, corpus level, after the usual Amharic normalisation
(Ge'ez homophones folded, punctuation dropped). Greedy is the model alone; the
second pair is with the language model included here.

| Test set | What it is | CER | WER | CER +LM | WER +LM |
|---|---|---:|---:|---:|---:|
| Our test set | 1,548 clips, 105 speakers, none of them in training | 0.0589 | 0.1870 | **0.0537** | **0.1611** |
| The same, down a phone line | 8 kHz A-law, what an IVR hears | 0.0633 | 0.1987 | **0.0573** | **0.1687** |
| Dialect | Addis Ababa, Gojjam, Wello | 0.0433 | 0.1732 | **0.0416** | **0.1606** |
| FLEURS am_et | public benchmark, read speech | 0.0628 | 0.1786 | **0.0599** | **0.1604** |
| Podcast, corrected by hand | spontaneous conversation | 0.2991 | 0.4964 | **0.2979** | **0.4707** |
| Conversation, held out | podcast episodes nothing trained on | 0.0659 | 0.1959 | **0.0660** | **0.1811** |

For comparison, on the same test set and the same scoring, the strongest open
Amharic model we could find scores 0.1052 CER and 0.2770 WER, and on dialect
0.1327 and 0.3100. It is better than this model on spontaneous podcast speech
(0.2865 CER), where this one is close behind.

Everything above is reproducible from `eval/results.json`, which holds every
set, both decodes, and the clip counts.

## What it is not good at

**Spontaneous conversation.** Around 47% word error on podcast
speech: usable for search or for drafting a transcript a person will fix, not
for reading unattended.

**Numbers.** It spells them out, because its training text does. "12" comes
back as አስራ ሁለት. If you need digits, convert after.

**Punctuation and case.** It writes neither. Sentences come back as words.

**Overlapping speakers.** One voice at a time. Two people talking together
will come back mangled.

**Other languages.** Amharic only. Oromo, Tigrinya or English audio will
produce Amharic-looking nonsense rather than an error.

## What it learned from

880 hours of Amharic, every clip screened first for bandwidth,
loudness, clipping, silence, and agreement between the transcript it came with
and an independent model.

| Kind of speech | Hours |
|---|---:|
| Regional dialect speech, five regions | 477 |
| Read speech | 283 |
| Broadcast and interview | 34 |
| Recorded by contributors through a Telegram bot | 38 |
| Conversation, transcripts two independent models agreed on | 25 |
| Conversation corrected by people | 2 |

Kept on purpose: background noise, room echo, 8 kHz phone audio, dialects, and
clips up to a minute. Dropped: audio too band-limited to carry speech, clipped
recordings, clips with little speech in them, and transcripts that disagree
with their audio badly enough to be wrong text rather than hard audio.

## How it was built

A CTC fine-tune of `badrex/Ethio-ASR-multilingual-600M` (wav2vec2-BERT, 600M
parameters), continued from an earlier fine-tune of ours rather than started
again. Two epochs over a fresh 60% of the training set each time, plus the
conversational data repeated, at 2e-5 with 300 warmup steps. Checkpoints were
chosen on read speech and conversation together, on development data.

30% of training clips were passed through an 8 kHz A-law round trip, which is
why the phone line row above is close to the clean one.

Two details that mattered more than they sound. One source ships its
transcripts with prefixes and suffixes split off as separate words, which teaches
spacing Amharic does not use; those were rejoined. And any training target
containing a digit was dropped, so the model has one convention for numbers
rather than two.

Trained on one H100 for about ten hours.

## Known and measured, not guessed

Every number here comes from a run whose logs, per clip outputs and settings
are kept. If you find it does something we did not describe, tell us: the gaps
we know about are written above, and the ones we do not know about are worth
more to us than the ones we do.

## Licence

CC BY 4.0. Use it for anything, including commercially, and say where it came
from. The model this one was fine-tuned from is CC BY 4.0, so these weights
carry the same terms; the attribution it asks for is in "How it was built"
above.

The training corpus is not released with the model and is not covered by this
licence.

Built in Addis Ababa by Chapi and the Dataset.ET contributors.
