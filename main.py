import sys
import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QProgressBar, QComboBox, QMessageBox
)

# Verileri proje klasöründe saklar.
DB_PATH = Path(__file__).resolve().parent / "lifexp.db"

# Bunlar uygulama için hazırlanmış özgün motivasyon cümleleridir.
SOZLER = [
    "Küçük adımlar da seni ileri taşır.",
    "Bugünkü emeğin, yarınki gücündür.",
    "Başlamak bir adımdır; devam etmek bir beceridir.",
    "Her gün mükemmel olmak zorunda değilsin.",
    "Kendine verdiğin her söz, yeni bir başlangıçtır.",
    "İlerlemeni başkalarının hızıyla ölçme.",
    "Bugün yaptığın küçük şeyleri küçümseme.",
]


class LifeXP(QWidget):
    def __init__(self):
        super().__init__()

        self.db = sqlite3.connect(DB_PATH)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                xp INTEGER NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.db.commit()

        self.setWindowTitle("LifeXP — Yiğit'in Macerası")
        self.resize(720, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("LifeXP")
        title.setObjectName("title")
        layout.addWidget(title)

        layout.addWidget(QLabel("Her tamamlanan görev, karakterini geliştirir."))

        self.character = QLabel()
        self.character.setObjectName("character")
        layout.addWidget(self.character)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        entry = QHBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Yeni görev: 30 dakika İngilizce çalış")
        self.task_input.returnPressed.connect(self.add_task)
        entry.addWidget(self.task_input)

        self.difficulty = QComboBox()
        self.difficulty.addItem("Kolay · 10 XP", 10)
        self.difficulty.addItem("Orta · 25 XP", 25)
        self.difficulty.addItem("Zor · 50 XP", 50)
        entry.addWidget(self.difficulty)

        add_button = QPushButton("Ekle")
        add_button.clicked.connect(self.add_task)
        entry.addWidget(add_button)

        layout.addLayout(entry)
        layout.addWidget(QLabel("GÖREVLERİN"))

        self.tasks = QListWidget()
        self.tasks.setWordWrap(True)
        layout.addWidget(self.tasks)

        complete_button = QPushButton("Seçili görevi tamamla  ✓")
        complete_button.clicked.connect(self.complete_task)
        layout.addWidget(complete_button)

        self.stats = QLabel()
        layout.addWidget(self.stats)

        layout.addWidget(QLabel("AÇILAN SÖZ KARTLARIN"))

        self.cards = QListWidget()
        self.cards.setWordWrap(True)
        layout.addWidget(self.cards)

        self.setStyleSheet("""
            QWidget {
                background-color: #111827;
                color: #e5e7eb;
                font-family: -apple-system, sans-serif;
                font-size: 14px;
            }
            QLabel#title {
                font-size: 36px;
                font-weight: bold;
                color: #a78bfa;
            }
            QLabel#character {
                font-size: 21px;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QListWidget {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #4c1d95;
            }
            QPushButton {
                background-color: #7c3aed;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8b5cf6;
            }
            QProgressBar {
                background-color: #1f2937;
                border: none;
                border-radius: 8px;
                text-align: center;
                min-height: 24px;
            }
            QProgressBar::chunk {
                background-color: #7c3aed;
                border-radius: 8px;
            }
        """)

        self.refresh()

    def refresh(self):
        rows = self.db.execute(
            "SELECT id, title, xp, done FROM tasks ORDER BY done, id DESC"
        ).fetchall()

        total_xp = sum(row[2] for row in rows if row[3])
        completed = sum(row[3] for row in rows)
        level = total_xp // 100 + 1

        self.character.setText(
            f"Yiğit  •  Seviye {level}  •  Toplam {total_xp} XP"
        )
        self.progress.setValue(total_xp % 100)
        self.progress.setFormat(f"{total_xp % 100} / 100 XP")
        self.stats.setText(
            f"{completed} görev tamamlandı  •  "
            f"{len(rows) - completed} görev bekliyor"
        )

        self.tasks.clear()

        for task_id, title, xp, done in rows:
            mark = "✓" if done else "○"
            item = QListWidgetItem(f"{mark}  {title}    +{xp} XP")
            item.setData(Qt.ItemDataRole.UserRole, task_id)
            self.tasks.addItem(item)

        self.cards.clear()
        unlocked = min(completed, len(SOZLER))

        for text in SOZLER[:unlocked]:
            self.cards.addItem(f"✦  {text}")

        if unlocked == 0:
            self.cards.addItem("İlk söz kartın için bir görev tamamla.")

    def add_task(self):
        title = self.task_input.text().strip()

        if not title:
            return

        xp = self.difficulty.currentData()

        with self.db:
            self.db.execute(
                "INSERT INTO tasks (title, xp) VALUES (?, ?)",
                (title, xp)
            )

        self.task_input.clear()
        self.refresh()
        self.task_input.setFocus()

    def complete_task(self):
        item = self.tasks.currentItem()

        if item is None:
            QMessageBox.information(
                self, "Görev seç", "Önce listeden bir görev seç."
            )
            return

        task_id = item.data(Qt.ItemDataRole.UserRole)
        task = self.db.execute(
            "SELECT xp, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

        if task is None or task[1]:
            QMessageBox.information(
                self, "Tamamlandı", "Bu görevin XP'sini zaten kazandın."
            )
            return

        previous_xp = self.db.execute(
            "SELECT COALESCE(SUM(xp), 0) FROM tasks WHERE done = 1"
        ).fetchone()[0]

        with self.db:
            self.db.execute(
                "UPDATE tasks SET done = 1 WHERE id = ? AND done = 0",
                (task_id,)
            )

        completed = self.db.execute(
            "SELECT COUNT(*) FROM tasks WHERE done = 1"
        ).fetchone()[0]

        message = f"+{task[0]} XP kazandın!"

        if (previous_xp + task[0]) // 100 > previous_xp // 100:
            message += "\n\nSeviye atladın!"

        if completed <= len(SOZLER):
            message += f"\n\nYeni söz kartın:\n“{SOZLER[completed - 1]}”"

        self.refresh()
        QMessageBox.information(self, "Görev tamamlandı!", message)

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LifeXP()
    window.show()
    sys.exit(app.exec())
