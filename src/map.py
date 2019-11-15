import re
import random
import json
import jinja2

JS_CODE = """
draw_functions = {

    "Placemark": function (map, obj) {
        properties = {
            hintContent: obj.hint,
            balloonContent: obj.content
        };
        options = {};
        if ('preset' in obj) {
            options['preset'] = obj.preset;
        }
        if ('iconColor' in obj) {
            options['iconColor'] = obj.iconColor
        }
        map.geoObjects.add(
            new ymaps.Placemark(obj.point, properties, options)
        );
    },
    "Route": function (map, obj) {
        params = {routingMode: obj.routingMode}
        referencePoints = {referencePoints: obj.referencePoints, params: params}


        map.geoObjects.add(
            new ymaps.multiRouter.MultiRoute(referencePoints)
        );
    }

}

function show_map(id, map_data) {
    ymaps.ready(init);

    var myMap;

    function init() {

        myMap = new ymaps.Map(id, map_data.state);

        map_data.objects.forEach(
            function (obj) {
                draw_func = draw_functions[obj.type];
                draw_func(myMap, obj);
            }
        );

    }

}
"""
TEMPLATE_HTML = jinja2.Template("""
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <script src="https://api-maps.yandex.ru/2.1/?lang=ru_RU&amp;apikey=63e33a98-598b-40df-8d99-1678d04be4bf"
            type="text/javascript"></script>
    <script type="text/javascript">
        show_map("{{ container_id }}", {{ map_json }});
        {{ js_code }}
    </script>
    <style>
        html, body, #map {
            width: 100%;
            height: 100%;
            padding: 0;
            margin: 0;
        }
    </style>
</head>
<body>

<div id="{{ container_id }}" style="width: {{ width }}px; height: {{ height }}px"></div>

</body>
</html>
""")


class Map(object):

    def __init__(self, center=[55.7520256, 48.7445183], zoom=15):
        """

        :param center: (list) [широта(float), долгота(float)] Географические координаты центра отображаемой карты
        :param zoom: (int) Масштаб.
        """
        self.center = center
        self.zoom = zoom
        self.objects = []

    def set_state(self, center, zoom):
        self.center = center
        self.zoom = zoom

    def _add_object(self, obj):
        self.objects.append(obj)

    def add_placemark(self, point, hint=None, content=None, preset='islands#icon', icon_color=None):
        """
        Добавляет метку на карту
        :param point: (list) [широта(float), долгота(float)]
        :param hint: (str)  содерижмое подсказки
        :param content: (str) содерижмое всплывающего облака
        :param preset: (str) ключ предустановленных стилей метки. Возможные варианты:
            'islands#icon'
            'islands#dotIcon'
            'islands#circleIcon'
            'islands#circleDotIcon'
        :param icon_color: (str) цвет иконки метки, например '#735184'
        :return:
        """
        obj = {
            'type': 'Placemark',
            'point': point,
            'hint': hint,
            'content': content
        }

        if icon_color:
            obj['iconColor'] = icon_color

        if preset:
            obj['preset'] = preset

        self._add_object(obj)

    def add_route(self, start_point, end_point, via_points=None, routing_mode='pedestrian'):
        """
        Добавить мультимаршрут на карте. Позволяет отображать на карте маршрут и несколько альтернатив к нему
        :param start_point: (list) [широта(float), долгота(float)]
        :param end_point: (list) [широта(float), долгота(float)]
        :param via_points: (list) [[широта(float), долгота(float)],...]
        :param routing_mode: Тип маршрутизации. Может принимать одно из двух строковых значений:
            "auto" — автомобильная маршрутизация;
            "masstransit" - маршрутизация с использованием общественного транспорта.
            "pedestrian" — пешеходная маршрутизация.
            "bicycle" - велосипедный маршрут.
        :return:
        """
        points = [start_point]
        if via_points is not None:
            points.extend(via_points)
        points.append(end_point)
        obj = {
            'type': 'Route',
            'referencePoints': points,
            'routingMode': routing_mode
        }

        self._add_object(obj)

    def _to_dict(self):
        return {
            'state': {
                'center': self.center,
                'zoom': self.zoom,
            },
            'objects': self.objects,
        }

    def _to_html(self, width=640, height=480, resizeable=False, container_id=None):
        if container_id is None:
            container_id = 'map_' + str(int(random.random() * 1E10))
        elif re.search('\s', container_id):
            raise ValueError("container_id must not contain spaces")

        map_dict = self._to_dict()

        html = TEMPLATE_HTML.render(
            container_id=container_id,
            width=width,
            height=height,
            resizeable=resizeable,
            map_json=json.dumps(map_dict),
            js_code=JS_CODE,
        )

        return html

    def save_html(self, file_path):
        """
        Сохраняет карту как html файл
        :param file_path:
        :return:
        """
        with open(file_path, 'w') as file:
            file.write(self._to_html())


"""Example"""
# map = Map()
# map.add_placemark([55.7550256, 48.7445183], hint='Заказ 1', icon_color="#ff0000")
# map.add_placemark([55.7550256, 48.7455183], hint='Заказ 1', icon_color="#0000ff")
# map.add_route([55.7550256, 48.7455183],[55.7550256, 48.7445183])
# map.save_html('map.html')
