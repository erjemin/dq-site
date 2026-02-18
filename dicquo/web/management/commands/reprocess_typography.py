from django.core.management.base import BaseCommand
from web.models import TbDictumAndQuotes
try:
    from etpgrf.typograph import Typographer
    from etpgrf.layout import LayoutProcessor
    from etpgrf.hyphenation import Hyphenator
except ImportError:
    print("Ошибка: библиотека etpgrf не найдена. Пожалуйста, установите её через 'poetry add etpgrf'")
    Typographer = None

class Command(BaseCommand):
    help = 'Переобрабатывает все цитаты через etpgrf с "санитайзером" и "висячей пунктуацией: слева"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Запустить без сохранения изменений в БД',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Ограничить количество обрабатываемых записей',
        )

    def handle(self, *args, **options):
        if not Typographer:
            self.stdout.write(self.style.ERROR('Библиотека Etpgrf отсутствует.'))
            return

        # Настройки типографа (как просил пользователь)
        # 1. Layout
        layout = LayoutProcessor(
            langs=['ru'],
            process_initials_and_acronyms=True,
            process_units=True
        )

        # 2. Hyphenation
        hyphenation = Hyphenator(
            langs=['ru'],
            max_unhyphenated_len=12
        )

        settings = {
            'langs': ['ru'],
            'process_html': True, # Обрабатываем как HTML (чтобы не ломать структуру, если она есть)
            'quotes': True,
            'layout': layout,
            'unbreakables': True,
            'hyphenation': hyphenation,
            'symbols': True,
            'hanging_punctuation': 'left', # ВАЖНО: Слева
            'mode': 'mixed',
            'sanitizer': 'etp', # ВАЖНО: Санитайзинг включен (очистит старую разметку)
        }

        self.stdout.write(f"Настройка Типографа с параметрами: {settings}")
        typographer = Typographer(**settings)

        qs = TbDictumAndQuotes.objects.all()
        if options['limit']:
            qs = qs[:options['limit']]

        count = qs.count()
        self.stdout.write(f"Найдено {count} цитат для обработки...")

        processed_count = 0

        for dq in qs:
            try:
                # Берем исходный текст.
                # Если в szContent уже лежит старый HTML (Муравьев), санитайзер 'etp' его вычистит.
                source_text = dq.szContent

                if not source_text:
                    continue

                new_html = typographer.process(source_text)

                # Обрабатываем intro если есть
                new_intro_html = ""
                if dq.szIntro:
                    new_intro_html = typographer.process(dq.szIntro)

                if options['dry_run']:
                    self.stdout.write(f"[{dq.id}] Будет обновлено. Предпросмотр: {new_html[:50]}...")
                else:
                    dq.szContentHTML = new_html
                    if new_intro_html:
                        dq.szIntroHTML = new_intro_html

                    # Сохраняем в обход метода save(), чтобы не триггерить ничего лишнего,
                    # или вызываем save(), если там теперь пусто (в нашей новой моделе save пустой).
                    # Используем update_fields для скорости.
                    dq.save(update_fields=['szContentHTML', 'szIntroHTML'])

                processed_count += 1
                if processed_count % 10 == 0:
                    self.stdout.write(f"Обработано {processed_count}/{count}...", ending='\r')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка обработки id={dq.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nГотово! Обработано {processed_count} цитат."))
