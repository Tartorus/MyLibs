from io import BytesIO
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.platypus import Spacer, SimpleDocTemplate, Paragraph, Table

DEFAULT_SPACER = Spacer(0, 24)


class PStyle:
    """
    Класс задает стиль параграфов
    """

    def __init__(self):
        self.path = os.path.dirname(__file__)
        self.fonts = set()

        self.font_register('TimesNewRomanRegular.ttf')\
            .font_register('TimesNewRomanBold.ttf')\
            .font_register('TimesNewRomanItalic.ttf')

        self.add_style('TimesNewRomanRegular', 'default_regular_center', alignment=1)\
            .add_style('TimesNewRomanRegular', 'default_regular')\
            .add_style('TimesNewRomanRegular', 'default_regular_right', alignment=2)\
            .add_style('TimesNewRomanBold', 'default_bold')\
            .add_style('TimesNewRomanBold', 'default_bold_center', alignment=1)\
            .add_style('TimesNewRomanBold', 'default_bold_right', alignment=2)\
            .add_style('TimesNewRomanItalic', 'default_italic')

    def font_register(self, font_name, path=None, add_style=False):
        """
        Регистрирует шрифты
        :return:
        """
        name = font_name.split('.')[0]
        if name in self.fonts:
            return self

        if path is None:
            path = self.path
        pdfmetrics.registerFont(ttfonts.TTFont(name, path+'/'+font_name))
        self.fonts.add(name)

        if add_style:
            self.add_style(name)

        return self

    def add_style(self, font_name, paragraph_name=None, alignment=0, font_size=12, **kwargs):
        """
        Метод добавляет стили. Если имя стиля параграфа не указывается, то за него принимается имя шрифта.
        Обратиться к объекту стиля можно по аттрибуту с именем параграфа в нижнем регистре.
        :param font_name:
        :param paragraph_name: <str>
        :param alignment: <int> 0 - left, 1 - center, 2 - right
        :param font_size: <int> - размер шрифта
        :return:
        """
        if paragraph_name is None:
            paragraph_name = font_name

        if kwargs.get('leading') is None:
            kwargs['leading'] = font_size
        attr_name = paragraph_name.lower()
        setattr(self, attr_name, ParagraphStyle(paragraph_name, fontSize=font_size, **kwargs))
        getattr(self, attr_name).fontName = font_name
        getattr(self, attr_name).alignment = alignment
        return self


class PdfCreator:

    def __init__(self, pstyles=None, album_orientation=False, **kwargs):
        self.buf = BytesIO()
        page_size = A4
        if album_orientation:
            page_size = landscape(A4)
        self.doc = SimpleDocTemplate(self.buf,
                                     pagesize=page_size,
                                     leftMargin=30*mm,
                                     rightMargin=10*mm,
                                     topMargin=20*mm,
                                     bottomMargin=20*mm,
                                     **kwargs
                                     )
        if pstyles is None:
            pstyles = PStyle()
        self.pstyles = pstyles
        self.content = list()

    def __getattr__(self, item):
        return getattr(self.doc, item)

    def build(self):
        """
        Формирование документа и возврат
        :return:
        """
        self.doc.build(self.content)
        return self.buf.getvalue()

    def add_header(self, document_header_1, content, document_header_2=None, document_header_2_style=None,
                   content_style=None, sign=None, sign_style=None, header_style=None, document_header_1_style=None,
                   header_title=None, add_header=True, timestamp=None):
        """
        Создает шапку документа
        :param document_header_1: <str> Основной заголовок документа
        :param document_header_1_style:  стиль титульника <PStyle>
        :param header_title: заголовок таблицы шапки документа
        :param header_style: стиль заголовка <PStyle>
        :param content: содержание заголовка [<str>,...]
        :param content_style: стиль содержания таблицы <PStyle>
        :param sign: подпись
        :param sign_style: стиль подписи <PStyle>
        :param timestamp: <str>
        :param add_header: <bool> автоматически добавляет заголовок в контент всего документа
        :return: возвращает все содержимое заголовка [ ... ]
        """
        header_content = list()

        if content_style is None:
            content_style = self.pstyles.default_regular

        if document_header_1_style is None:
            document_header_1_style = self.pstyles.default_bold_center

        if header_title:
            if header_style is None:
                header_style = self.pstyles.default_regular_center
            header_title = [['', header_title]]

        # шапка
        table_content = [['', c, ''] for c in content]
        header_content.append(self.add_table(table_content,
                                             header_style=header_style,
                                             content_style=content_style,
                                             headers=header_title,
                                             colWidths=[250, 170, 80],
                                             add_table=False))

        # подпись утверждающего
        if sign:
            if sign_style is None:
                sign_style = self.pstyles.default_regular_right
            header_content.append(Paragraph(sign, sign_style))

        # добавление даты утверждения
        if timestamp:
            table_content = [['', timestamp, '']]
            header_content.append(self.add_table(table_content,
                                                 content_style=content_style,
                                                 colWidths=[250, 170, 80],
                                                 add_table=False))

        header_content.append(Spacer(0, 20))
        header_content.append(Paragraph(document_header_1, document_header_1_style))

        if document_header_2:
            if document_header_2_style is None:
                document_header_2_style = self.pstyles.default_regular_center
            header_content.append(Paragraph(document_header_2, document_header_2_style))
        header_content.append(Spacer(0, 20))

        if add_header:
            self.content.extend(header_content)

        return header_content

    def add_bottom(self, content, content_style=None, sign=None, sign_style=None, add_bottom=True):
        """
        Добавляет "низ" документа
        :param content: [<str>, ... ]
        :param content_style: <PStyle>
        :param add_bottom: <bool>
        :return:
        """
        if content_style is None:
            content_style = self.pstyles.default_regular

        bottom_content = [Paragraph(c, content_style) for c in content]

        if sign:
            if sign_style is None:
                sign_style = self.pstyles.default_regular_right
            bottom_content.append(Paragraph(sign, sign_style))

        if add_bottom:
            self.content.extend(bottom_content)
        return bottom_content

    def add_table(self, content, headers=None, header_style=None, content_style=None, add_table=True, style=None, **table_args):
        """
        Функция создает таблицу в пдф и заполняет ее контентом
        :param headers: заголовки таблицы
        :param header_style: стиль заголовков таблицы
        :param content:
        :param content_style: стиль контента
        :param table_args:
        :return:
        """
        table_content = []
        if header_style is None:
            header_style = self.pstyles.default_regular_center
        if content_style is None:
            content_style = self.pstyles.default_regular_center
        if headers:
            [table_content.append([Paragraph(p, header_style) for p in row]) for row in headers]

        [table_content.append([Paragraph(p, content_style) for p in row]) for row in content]
        table = Table(table_content, style=style, **table_args)

        if add_table:
            self.content.append(table)
            self.content.append(Spacer(0, 20))
        return table

    def add_line(self, row, style=None):
        """
        Задает каждой ячейке строки определенный стиль
        :param row: [<str>, ...]
        :param style:
        :return:
        """
        if style is None:
            style = self.pstyles.default_regular
        return [Paragraph(cell, style) for cell in row]