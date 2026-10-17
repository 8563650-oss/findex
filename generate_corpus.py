import random
from pathlib import Path

def generate_tech_corpus(output_dir="data", num_files=1000, file_size_kb=50):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    tech_terms = [
        "YOLOv5", "YOLOv8 architecture", "NMS threshold", "FAISS index", "HNSW graph", 
        "LPIPS metric", "RTSP stream", "Wireshark packet dump", "Ubuntu 22.04 LTS", 
        "SigmaStar dev board", "U-Boot parameters", "UART serial connection", 
        "Home Assistant Docker", "AI detection module", "QA VMS testing", 
        "frame slicing script", "Streamlit dashboard", "Ajax Systems hardware",
        "Chevrolet Cruze 2012 module"
    ]
    
    # Блок тексту приблизно на 1 КБ
    filler_block = (
        "process initialization started. validating configuration parameters. "
        "memory allocation successful. awaiting stream connection. "
        "buffer size optimized for current workload. checking dependencies. "
        "network interface ready. timeout threshold set. "
    ) * 6
    
    print(f"Створюємо {num_files} файлів у папці '{output_dir}/'...")
    
    for i in range(num_files):
        lines = []
        for _ in range(file_size_kb):
            # Додаємо кілька випадкових термінів у кожен кілобайт тексту
            terms = " ".join(random.choices(tech_terms, k=3))
            lines.append(filler_block + terms)
        
        file_path = Path(output_dir) / f"doc_{i+1:04d}.txt"
        file_path.write_text("\n".join(lines), encoding="utf-8")
        
    print(f"Готово! Корпус на ~{num_files * file_size_kb / 1024:.1f} МБ успішно згенеровано.")

if __name__ == "__main__":
    generate_tech_corpus()