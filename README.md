# ⚖️ AFIRGen – AI-based FIR Generation System

AFIRGen is an AI-powered system built to automate **First Information Report (FIR)** generation using real-world Indian legal data (BNS).  
It combines **Speech-to-Text (STT)**, **Optical Character Recognition (OCR)**, **Retrieval-Augmented Generation (RAG)**, and **Large Language Models (LLMs)** to create accurate, structured, and law-compliant FIR drafts in real time.

---

## 🧠 Overview
- Uses **Whisper** for speech-to-text and **Donut OCR** for image-to-text extraction.  
- Implements a **RAG pipeline** (with RAG model) to pull relevant BNS sections and contextual data.  
- Fine-tuned **LLaMA**, **Mistral**, and other open-weight LLMs on Indian Law and Alpaca-style datasets.  
- Integrates all components into a **modular FastAPI backend** connected to a **MySQL** database.  

---

## 🧩 Design Documents
- [📄 Design Document (PPT version)](https://www.dropbox.com/scl/fi/uqh8n3i9vfo0t3zq8bpsl/Design.pptx?rlkey=npz59jbcbgqjw819vjuax3mp9&st=lj6zfrx5&dl=0)  
- [📘 Design Document (PDF version)](https://www.dropbox.com/scl/fi/l2u33zvy8e76ahx5fv9ax/Design.pdf?rlkey=jnohv4villlx1i075bugz26io&st=n41qy9e7&dl=0)
- [🗄️ Database Configuration](./AFIRGEN%20FINAL/DATABASE.md)
- [🚀 Setup Guide](./AFIRGEN%20FINAL/SETUP.md)
- [🔒 Security Documentation](./AFIRGEN%20FINAL/SECURITY.md)

---

## 🔒 Security Features

AFIRGen implements comprehensive security measures to protect against common vulnerabilities:

- **HTTPS/TLS Encryption**: All traffic encrypted with TLS 1.2+ (see below)
- **CORS Protection**: Configurable allowed origins (no wildcards in production)
- **Rate Limiting**: 100 requests per minute per IP (configurable)
- **Input Validation**: XSS and SQL injection prevention
- **Authentication**: Timing-attack resistant with constant-time comparison
- **Security Headers**: X-Frame-Options, CSP, HSTS, and more
- **File Upload Security**: Size limits, MIME validation, secure filenames
- **Session Management**: UUID-based with automatic expiration

For detailed security information, see:
- [Security Documentation](./AFIRGEN%20FINAL/SECURITY.md)
- [Security Implementation Summary](./AFIRGEN%20FINAL/SECURITY-IMPLEMENTATION-SUMMARY.md)
- [Security Quick Reference](./AFIRGEN%20FINAL/SECURITY-QUICK-REFERENCE.md)

**Security Testing**: Run `python AFIRGEN\ FINAL/test_security.py` to validate security measures.

---

## 🔐 HTTPS/TLS Support

AFIRGen now supports HTTPS/TLS encryption for all traffic using an nginx reverse proxy:

- **TLS 1.2 and 1.3**: Modern encryption protocols only
- **Strong Cipher Suites**: Forward-secret, high-strength ciphers
- **HTTP to HTTPS Redirect**: Automatic redirect for all HTTP traffic
- **Security Headers**: HSTS, CSP, X-Frame-Options, and more
- **Let's Encrypt Support**: Free, automated certificates for production
- **Self-Signed Certificates**: Easy setup for development/testing

**Quick Setup (Development)**:
```bash
cd "AFIRGEN FINAL"
./scripts/generate-certs.sh  # Select option 1 for self-signed
docker-compose up -d
# Access: https://localhost
```

**Quick Setup (Production)**:
```bash
cd "AFIRGEN FINAL"
./scripts/generate-certs.sh  # Select option 2 for Let's Encrypt
docker-compose up -d
```

For detailed HTTPS/TLS information, see:
- [HTTPS/TLS Implementation Guide](./AFIRGEN%20FINAL/HTTPS-TLS-IMPLEMENTATION.md)
- [HTTPS/TLS Quick Reference](./AFIRGEN%20FINAL/HTTPS-TLS-QUICK-REFERENCE.md)
- [HTTPS/TLS Validation Checklist](./AFIRGEN%20FINAL/HTTPS-TLS-VALIDATION-CHECKLIST.md)

**HTTPS Testing**: Run `python AFIRGEN\ FINAL/test_https_tls.py` to validate HTTPS configuration.

---

## ⚡ Performance & Concurrency

AFIRGen is optimized to handle multiple concurrent requests efficiently:

- **Concurrent Request Handling**: Supports 10+ concurrent FIR generations
- **Connection Pooling**: HTTP/2 with persistent connections to model servers
- **Resource Management**: Semaphore-based concurrency control
- **Fast Response Times**: < 30 seconds per FIR generation
- **High Throughput**: 20-30 FIRs per minute under concurrent load

**Performance Features:**
- MySQL connection pool (15 connections)
- Shared HTTP client with connection pooling
- Parallel violation checking (70% faster)
- KB query caching with 5-minute TTL (80% faster on cache hits)
- Optimized token generation limits

For detailed performance information, see:
- [Concurrency Implementation](./AFIRGEN%20FINAL/CONCURRENCY-IMPLEMENTATION.md)
- [Concurrency Test Guide](./AFIRGEN%20FINAL/CONCURRENCY-TEST-GUIDE.md)
- [Performance Optimizations](./AFIRGEN%20FINAL/PERFORMANCE-OPTIMIZATIONS.md)

**Performance Testing**: 
- Single request: `python AFIRGEN\ FINAL/test_performance.py`
- Concurrent load: `python AFIRGEN\ FINAL/test_concurrency.py`

---

## 🧰 Tech Stack
**Python**, **FastAPI**, **LLaMA**, **Mistral**, **Whisper**, **Donut OCR**, **IndicBERT**, **MySQL**, **Docker**

---

## ⚙️ System Flow

Here’s the system architecture — showing how each module connects and processes data through the pipeline:

![AFIRGen Architecture](./assets/tempflowchartref.png)

---


## 🚀 Highlights
- Fine-tuned open-weight LLMs for **domain-specific legal accuracy**.  
- Backend optimized for **low-latency inference** and **real-time responses**.  
- Seamless integration of multiple AI modules for **end-to-end FIR automation**.

---

## 🔮 Future Work
- Refine the **frontend UX** for smoother interaction.  
- Add new features like case classification and legal section summarization.  
- Deploy the entire system to the **cloud** for scalable and public access (currently runs locally).

---

## 👥 Contributors
- **Navaneeth Kutty**  
- **Priyan M S K**

---

## 🏁 Summary
AFIRGen showcases how GenAI can transform the Indian legal process by automating complex document workflows — bridging AI, law, and real-world applications.

---
