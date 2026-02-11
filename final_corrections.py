# Финальные исправления с учетом замечаний

# Проверка скорректированных вариантов
titles_corrected = [
    ('article_rent.html', 'Проверка договора аренды онлайн бесплатно за 60 сек: 7 опасных пунктов'),
    ('mobile_app.html', 'DocScan App — мобильное приложение: проверка документов за 60 сек'),
]

print('=' * 80)
print('СКОРРЕКТИРОВАННЫЕ ВАРИАНТЫ')
print('=' * 80)
print()

for file, title in titles_corrected:
    length = len(title)
    if length <= 60:
        status = '[OK]'
    elif length <= 70:
        status = '[Допустимо]'
    else:
        status = '[Слишком длинный]'
    print(f'{file[:45]:45} | {length:2} симв. | {status}')
    print(f'  {title}')
    print()

