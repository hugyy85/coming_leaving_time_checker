# coming_leaving_time_checker

Сервис который вычисляет общее время пребывания всех людей за каждое
число.

## Deployment
Необходимо установить докер для запуска приложения
После установки открыть консоль в папке с проектом и ввести:

```
 docker build -t 2gis_coming_leaving_time .
 docker run -d --name 2gis_coming_leaving_time -p 80:80 2gis_coming_leaving_time
```

Сервис запустится на 80 порту вашей [локальной машины](http://127.0.0.1)
Пройдя по ссылке, вы можете загрузить проверяемый файл(например файлы из папки /test_data)
и посмотреть результаты моей работы


## Testing
Для проведения тестирования, после установки, необходимо ввести команду

`docker exec -it 2gis_coming_leaving_time pytest tests.py
`
 