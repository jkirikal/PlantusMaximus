from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from rest_framework.views import APIView
from rest_framework.response import Response
import sqlite3


class HomeView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'charts.html', {})

def get_data(request, *args, **kwargs):
    data = {
        "sales": 100,
        "customers": 10,
    }
    return JsonResponse(data)


class ChartData(APIView):


    def get(self, request, format=None):
        self.conn = sqlite3.connect('/home/pi/Dev/plantmax/src/datalogger.db')
        cursor = self.conn.cursor()
        self.querytemp = cursor.execute('SELECT rowid, aeg, protsent, kaugus FROM andmed ORDER BY rowid')
        self.conn.commit()
        labels = []
        niiskused = []
        protsendid = []
        kaugused = []
        protsendid2 = []
        labels2 = ['HETKE NIISKUSTASE', '---']
        for instance in self.querytemp:
            a = instance[2]
            niiskused.append(a)
            labels.append(instance[1])
            kaugused.append(instance[3])
        prots = niiskused[-1]
        kaugus = kaugused[-1]
        teineosa = 100 - prots
        kolmasosa = 100 - kaugus
        protsendid.append(prots)
        protsendid.append(teineosa)
        protsendid2.append(kaugus)
        protsendid2.append(kolmasosa)

        data = {
                "labels": labels,
                "niisk": niiskused,
                "labels2": labels2,
                "protsendid": protsendid,
                "kaugused": kaugused,
                "protsendid2": protsendid2
        }
        return Response(data)
