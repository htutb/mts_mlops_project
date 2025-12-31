Уваров Николай Романович

# Toxicity Detection Service

## Бизнес-ценность

Задача сервиса - определить, является ли пользовательский комментарий токсичным и вернуть вероятность токсичности.

Автоматическая модерация позволяет: 
- быстрее скрывать токсичные сообщения
- разгружать модераторов
- улучшать качество коммьюнити и удержание пользователей

## Стек проекта

- **ML**: TfidfVectorizer + LogisticRegression
- **Broker**: Apache Kafka (передача сообщений и предсказаний)
- **DB**: PostgreSQL (хранение текстов и результатов)
- **UI**: Streamlit (ввод данных и просмотр результатов)
- **Monitoring**: Grafana (метрики и дашборды)
- **Packaging**: Docker + Docker Compose

## Структура проекта
```
├── README.md            
├── docker-compose.yml !!!!!!!!
├── requirements.txt
├── assets/
│   ├── one_pager.pdf            # 1 страница описания сервиса   !!!!!!!!
│   └── architecture.png         # схема архитектуры
├── ml_worker/
│   ├── Dockerfile
│   ├── worker.py                # Kafka consumer -> predict -> Postgres 
│   ├── db.py                    # подключение к Postgres
│   └── model/
│       └── model_pipeline.joblib
├── sql/
│   └── init.sql                 # создание таблиц в Postgres
├── training/
│   └── train.py                 # offline обучение -> model_pipeline.joblib
├── ui/
│   ├── Dockerfile
│   ├── app.py                   # Streamlit UI
│   └── db.py
└── grafana/                     # Monitoring
    └── provisioning/
        ├── datasources/
        │   └── postgres.yml
        └── dashboards/
            ├── dashboard.yml
            └── toxicity_dashboard.json
```

## Запуск проекта

0. Требования
- Docker ≥ 20.x
- Docker Compose ≥ 2.x

1. Клонирование репозитория

```bash
git clone https://github.com/htutb/mts_mlops_project.git
cd mts_mlops_project
```

2. Сборка и запуск сервисов
```bash
docker-compose up -d
```

## Использование сервиса

### Streamlit UI

- В Docker перейти на http://localhost:8501
- Есть возможность ввести как и одиночный текст, так и прикрепить csv файл с указанными колонками (пример: check.csv в папке data)
- Получить вероятность токсичности и флаг, является ли сообщение токсичным

### Grafana

- В Docker перейти на http://localhost:3000
- Вввести логин и пароль (admin, admin соотвественно)
- Открыть дашборд с панелями

