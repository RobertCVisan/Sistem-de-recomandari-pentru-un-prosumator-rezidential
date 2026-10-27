
from flask import Flask,request, jsonify
import sqlite3
import time 

app = Flask(__name__)
def chk_con(conn):
    try:
        conn.cursor()
        return True
    except:
        return False
db_path='iriseCorect.sqlite3'
db_path2='Recomandari.db'
conn =sqlite3.connect(db_path)
conn2=sqlite3.connect(db_path2)
print(chk_con(conn))
dictionar_appliance_redundante = (6,8)
class Production_parameters:
    def __init__(self,P_M,n,f,G,G_tstc):
        self.P_M=P_M
        self.n=n
        self.f=f
        self.G=G
        self.G_tstc=G_tstc


#Aici am Productia mediana pentru fiecare ora intr-o zi,saptamana,luna,an
#pentru a calcula productia vom lua ca exemplu 5 panouri solare Panou solar fotovoltaic monocristalin LONGi 410W LR5-54HIH-410M cu variabilele:
#Pentru scopul acestei lucrari, si dat fiind ca nu am date legate de radiatia solara pentru fiecare casa, vom alege un exemplu de statie meteo care are date legate de radiate
#Aceaste statie va fi statia Perreux , Id 42170001 ,Longitudine 4.1033 Latidudine 46.02333,Starting EpochTime 52973200 si Ending EpochTime 978300000, cu speficicatia ca in baza noastra de date, luam valoarea 4 pentru radiatia solara si ignor ceilalti factori precum temperatura,umiditate,directia vantului si forta vantului, deoarece pentru productia de energie electrica, radiatia solara este factorul cel mai important.
# ADDENDUM, valorile am verificat sunt luate de la ora 6 din prima zi pana la ora 6 din a doua zi,atunci incepe startepochtime 
#Alta problema , datele legate de radiatie sunt sub media obisnuita, nu sunt sigur daca sunt valori corecte sau nu
P_M= 410 # Power of a module,410 watts
n=5 # number of modules
f=0.75 #scaling factor for real world conditions
G_Tstc=1000 #incident radation at Standard Temperature Conditions(1000 W/m2)
Production_query = '''Select Sum(R.value) as TotalProduction
                      From WeatherData R 
                      Inner Join WeatherStation W on R.WeatherStationIDREF=W.ID
                      Where W.ID=42170001 And R.Epochtime >= ? And R.EpochTime < ? And R.WeatherVariableIDREF=4'''
#informatie legata de casa,explicit id-ul acesteia dupa zipcode si locatie
@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Welcome to the House API! Use /house?zipcode=<zipcode>&location=<location> to get house ID.'})

@app.route('/house', methods=['GET'])
def get_house():
    zipcode = request.args.get('zipcode')
    location  = request.args.get('location')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = '''SELECT ID FROM House WHERE ZIPcode = ? AND Location = ?'''
    cur.execute(query, (zipcode, location))
    result = cur.fetchone()
    conn.close()
    if result:
        return jsonify({'ID': result[0]})
    else:
        return jsonify({'error': 'House not found'}), 404

#informatie legata de timpul de incepere si sfarsit al masuratorilor pentru o casa data
@app.route('/house/<int:house_id>/time', methods=['GET'])
def get_time(house_id):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = '''SELECT StartingEpochTime, EndingEpochTime FROM House WHERE ID = ?'''
    cur.execute(query, (house_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return jsonify({'StartingEpochTime': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(result[0])), 'EndingEpochTime': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(result[1]))},)
    else:
        return jsonify({'error': 'House not found'}), 404

    
#informatie legata de consumul total pe zi pentru fiecare APARAT pentru o casa data, pe baza id-ului acesteia si a zilei pentru care se doreste informatia
@app.route('/house/<int:house_id>/consumption', methods=['GET'])
def get_consumption(house_id):
    day=request.args.get('day',default=1 ,type=int)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = '''SELECT StartingEpochTime FROM House WHERE ID = ?'''
    start_time=cur.execute(query, (house_id,)).fetchone()
    if start_time is None:
        conn.close()
        return jsonify({'error': 'House not found'}), 404
    
    cur.execute('''Select SUM(C.Value) As TotalConsum,A.name,A.TypeIDREF 
                   From Consumption C 
                   inner join Appliance A on C.ApplianceIDREF=A.ID 
                   Inner Join ApplianceType At on A.TypeIDREF = At.ID
                   Where C.HouseIDREF=? And A.HouseIDREF=? And C.EpochTime >= ? And C.EpochTime < ? And A.TypeIDREF != ?   Group By A.name,A.TypeIDREF''',(house_id,house_id,start_time[0]+600*(day-1)*6*24,start_time[0]+600*day*6*24,8))
    result=cur.fetchall()
    conn.close()

    return jsonify([{'TotalConsum': row[0], 'name': row[1], 'TypeIDREF': row[2]} for row in result])
# Consumul Total Pentru o zi pentru o casa data,pe baza id-ului acesteia si a zilei 

@app.route('/house/<int:house_id>/consumption/total',methods=['GET'])
def get_total_consumption(house_id):
        day=request.args.get('day',default=1 ,type=int)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        query = '''SELECT StartingEpochTime FROM House WHERE ID = ?'''
        start_time=cur.execute(query, (house_id,)).fetchone()
        if start_time is None:
            conn.close()
            return jsonify({'error': 'House not found'}), 404
        
        cur.execute('''Select SUM(C.Value) As TotalConsum
                       From Consumption C 
                       inner join Appliance A on C.ApplianceIDREF=A.ID 
                       Inner Join ApplianceType At on A.TypeIDREF = At.ID
                       Where C.HouseIDREF=? And A.HouseIDREF=? And C.EpochTime >= ? And C.EpochTime < ? And A.TypeIDREF != ? ''',(house_id,house_id,start_time[0]+600*(day-1)*6*24,start_time[0]+600*day*6*24,8))
        result=cur.fetchone()
        conn.close()
        return jsonify([{'TotalConsum':result[0]}])
#Informatie legata de consumul pe Ora TOTAL pentru o casa data, pe baza id-ului acesteia si a zilei pentru care se doreste informatia

@app.route('/house/<int:house_id>/consumption/<int:day>', methods=['GET'])
def get_consumption_by_hour(house_id,day):
    hour=request.args.get('hour',default=1 ,type=int)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query='''SELECT StartingEpochTime FROM House WHERE ID = ?'''
    start_time=cur.execute(query, (house_id,)).fetchone()
    if start_time is None:
        conn.close()
        return jsonify({'error': 'House not found'}), 404
    if hour < 1 or hour > 24:
        conn.close()
        return jsonify({'error': 'Hour must be between 1 and 24'}), 403
    
    cur.execute('''SELECT SUM(C.Value) as TotalConsum                   
                   From Consumption C
                   Inner Join Appliance A on C.ApplianceIDREF=A.ID And on C.HouseIDREF=A.HouseIDREF
                   Where C.HouseIDREF=? AND C.EpochTime >= ? AND C.EpochTime < ? And A.TypeIDREF != ?''',(house_id,start_time[0]+600*(day-1)*6*24+(hour-1)*3600,start_time[0]+600*(day-1)*6*24+hour*3600,8))
    result=cur.fetchone()
    consumul_ora=result[0]
    conn.close()
    return jsonify({'TotalConsum': result[0] if result[0] is not None else 0,'hour':hour,'day':day})

#Productia totala per zi
@app.route('/house/<int:house_id>/production', methods=['GET'])
def get_production(house_id):
    day =request.args.get('day', default =1,type=int)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query='''SELECT StartingEpochTime FROM House WHERE ID = ?'''
    start_time=cur.execute(query, (house_id,)).fetchone()
    if start_time is None:
            conn.close()
            return jsonify({'error': 'House not found'}), 404
    cur.execute(Production_query,(start_time[0]+600*(day-1)*6*24,start_time[0]+600*day*6*24))
    Production_result=cur.fetchone()
    conn.close()
    p1 = Production_parameters(410,n,f,Production_result[0],G_Tstc)
    TotalProduction=p1.f*p1.n*p1.P_M*p1.G/p1.G_tstc
    return jsonify({'TotalProduction': TotalProduction if TotalProduction is not None else 0,'day':day,'StartingEpochTime':start_time[0]+(day-1)*3600*24,'Real_Time':time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time[0]+(day-1)*3600*24))})
#Calcul index Self Sufficiency pe zi, cat consum din productia mea si cata energie provine din productia mea si cata energie iau din exterior

@app.route('/house/<int:house_id>/self_sufficiency_consumption',methods=['GET'])
def get_self_sufficiency(house_id):
    day=request.args.get('day',default=1,type=int)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query='''SELECT StartingEpochTime FROM House WHERE ID = ?'''
    start_time=cur.execute(query, (house_id,)).fetchone()
    if start_time is None:
        conn.close()
        return jsonify({'error': 'House not found'}), 404
    each_hour_total_consumption_query='''SELECT SUM(C.Value) as TotalConsum,((C.EpochTime-?)/3600) as Hour                  
                   From Consumption C
                   Inner Join Appliance A on C.ApplianceIDREF=A.ID And C.HouseIDREF=A.HouseIDREF
                   Where C.HouseIDREF=? AND C.EpochTime >= ? AND C.EpochTime < ? And A.TypeIDREF != ?
				   Group By Hour
				   Order By Hour'''
    cur.execute(each_hour_total_consumption_query,(start_time[0]+(day-1)*24*3600,house_id,start_time[0]+(day-1)*24*3600,start_time[0]+day*24*3600,8))
    consumption_each_hour_result=cur.fetchall()
    each_hour_total_radiation_query='''Select R.value as TotalProduction,((R.EpochTime-?)/3600) as Hour
                      From WeatherData R 
                      Inner Join WeatherStation W on R.WeatherStationIDREF=W.ID
                      Where W.ID=42170001 And R.Epochtime >= ? And R.EpochTime < ? And R.WeatherVariableIDREF=4 
                      Order By Hour
                      '''
    cur.execute(each_hour_total_radiation_query,(start_time[0]+(day-1)*24*3600,start_time[0]+(day-1)*24*3600,start_time[0]+day*24*3600))
    each_hour_total_radiation_result=cur.fetchall()
    conn.close()
    total_hourly_production=[]
    Self_sufficiency=0
    Min_sum=0
    Consumption_sum=0
    Production_sum=0
    for i in range(24):
        hourly_production=410*n*f*each_hour_total_radiation_result[i][0]/G_Tstc
        total_hourly_production.append(hourly_production)
        if(total_hourly_production[i]<consumption_each_hour_result[i][0]) :Min_sum=Min_sum+total_hourly_production[i]
        else:Min_sum=Min_sum+consumption_each_hour_result[i][0]
        Consumption_sum=consumption_each_hour_result[i][0]+Consumption_sum
        Production_sum=total_hourly_production[i]+Production_sum

    Self_sufficiency=Min_sum/Consumption_sum
    Self_consumption=Min_sum/Production_sum                                                                             
    return jsonify({'Self_sufficiency':Self_sufficiency ,
                    'Self_consumption':Self_consumption ,
                     'Hourly_Data':[{
                        'Hourly_Consumption':consumption_each_hour_result[i][0],
                        'Hourly_Production':total_hourly_production[i],
                        'hour':each_hour_total_radiation_result[i][1],
                        'EpochTime':start_time[0]+(day-1)*24*3600,
                        'Real_Time':time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time[0]+(day-1)*24*3600+each_hour_total_radiation_result[i][1]*3600))}
                    for i in range(24)]
                     })


#Api pentru recomandari,logica recomandari
@app.route('/house/<int:house_id>/recommendations', methods=['GET'])
def get_recommendation(house_id):
    day=request.args.get('day',default=1,type=int)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query='''SELECT StartingEpochTime FROM House WHERE ID = ?'''
    start_time=cur.execute(query, (house_id,)).fetchone()
    if start_time is None:
        conn.close()
        return jsonify({'error': 'House not found'}), 404
    each_hour_total_consumption_query='''SELECT SUM(C.Value) as TotalConsum,((C.EpochTime-?)/3600) as Hour                  
                   From Consumption C
                   Inner Join Appliance A on C.ApplianceIDREF=A.ID And C.HouseIDREF=A.HouseIDREF
                   Where C.HouseIDREF=? AND C.EpochTime >= ? AND C.EpochTime < ? And A.TypeIDREF != ?
                   Group By Hour
                   Order By Hour'''
    cur.execute(each_hour_total_consumption_query,(start_time[0]+(day-1)*24*3600,house_id,start_time[0]+(day-1)*24*3600,start_time[0]+day*24*3600,8))
    consumption_each_hour_result=cur.fetchall()
    each_hour_total_radiation_query='''Select R.value as TotalProduction,((R.EpochTime-?)/3600) as Hour
                      From WeatherData R 
                      Inner Join WeatherStation W on R.WeatherStationIDREF=W.ID
                      Where W.ID=42170001 And R.Epochtime >= ? And R.EpochTime < ? And R.WeatherVariableIDREF=4 
                      Order By Hour
                      '''
    cur.execute(each_hour_total_radiation_query,(start_time[0]+(day-1)*24*3600,start_time[0]+(day-1)*24*3600,start_time[0]+day*24*3600))
    each_hour_total_radiation_result=cur.fetchall()

#Dictionar Recomandari
    Recommendation_list={
        "1":"Your consumption level is 0",
        "2":"Your system is in a production surplus, if you need to use more devices please do so at this hour",
        "3":"Your systems consumption level is slightly above the production, production to consumption ratio is inbetween 90 and 100%, prod/cons>=0.9 ",
        "4":"Your energy production  to consumption ratio is '10%'  at this hour,if you have no need for some devices disconnect them now prod/cons <=0.1",
        "5":"Your energy production is the same as the consumption,keep it up ",
        "6":"Your production level is 0",
        "7":" energia utilizata depaseste productia , dar diferenta este moderata"
    }
    Recommendations=[]
    total_hourly_production=[]
    for i in range(24):
            hourly_production=410*n*f*each_hour_total_radiation_result[i][0]/G_Tstc
            total_hourly_production.append(hourly_production)
            if(hourly_production and consumption_each_hour_result):
                if(consumption_each_hour_result[i][0]==0):Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':1})
                elif(hourly_production>consumption_each_hour_result[i][0]): Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':2})
                elif(hourly_production<consumption_each_hour_result[i][0]): 
                    if(hourly_production/consumption_each_hour_result[i][0]<=0.1) : Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':4}) 
                    elif(hourly_production/consumption_each_hour_result[i][0]>=0.9):Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':3})
                    else:Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':7}) 
                else: Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':5}) 
            elif(hourly_production==0):Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':6})
            else:Recommendations.append({'hour':each_hour_total_radiation_result[i][1],'Recommendation_type':1})
    Ore_surplus=[]
    Ore_prod_cons_aprox_egal=[]#ore in care consumul si productia sunt aproape la fel , intr-un interval de 10 %
    Ore_prod_cons_foarte_negativ=[]#ore in care consumul este mult mai mare decat productia, deobicei noaptea
    Ore_prod_cons_egal=[]#ore in care consumul si productia de energie sunt egale
    Ore_produs_0=[]
    Ore_consum_0=[]
    Ore_prod_cons_negativ=[]#ore in care consumul este mai mare decat productia dar intre 10 % si 90%
    for h in Recommendations:
        match h['Recommendation_type']:
            case 1:
                 Ore_consum_0.append(h['hour'])
            case 2:
                Ore_surplus.append(h['hour'])
            case 3:
                Ore_prod_cons_aprox_egal.append(h['hour'])
            case 4:
                Ore_prod_cons_foarte_negativ.append(h['hour'])
            case 5:
                Ore_prod_cons_egal.append(h['hour'])
            case 6:
                Ore_produs_0.append(h['hour'])
            case 7:
                Ore_prod_cons_negativ.append(h['hour'])
    mesaje_specifice=[]
    tipuri_mesaje=[
        (Ore_consum_0," consumul va fi 0"),
        (Ore_surplus," productia va depasi consumul.Puteti folosi mai multe aparate la aceste ore"),
        (Ore_prod_cons_aprox_egal," productia va fi aproape egala cu consumul, diferenta dintre ele fiind de 10%"),
        (Ore_prod_cons_foarte_negativ," productia va fi  mult mai mica decat consumul, incercati sa opriti aparatele neutilizate"),
        (Ore_prod_cons_egal," consumul si productia vor fi egale,mentineti stabilitatea"),
        (Ore_produs_0," productia va fi 0"),
        (Ore_prod_cons_negativ," energia utilizata va depasi productia , dar diferenta este moderata")
    ]

    def func_consec(lista): #functie pentru a vedea daca lista are ore consecutive
        consec=1#variabila contor pentru a vedea daca lista are ore consecutive
        for i in range(len(lista)-1):
            if(lista[i+1]-lista[i]!=1): consec=0
        return consec

    def ora_reala(ora):
        return time.strftime('%H:%M', time.gmtime(start_time[0]+(day-1)*24*3600+ora*3600))
    type_of_message=1#tipul de mesaj, nevoie de el pentru a diferentia dintre mesaje si pentru a apela tipul specific de mesaj in aplicatie    
    for Ore_lista,lista_mesaje in tipuri_mesaje:    
        if (Ore_lista): 
            ore=",".join(ora_reala(h) for h in Ore_lista)
            if len(Ore_lista)>3 and func_consec(Ore_lista): mesaje_specifice.append({"Message":f"in intervalul orar [{ora_reala(Ore_lista[0])}--{ora_reala(Ore_lista[-1]+1)}]{lista_mesaje} ","MessageType":type_of_message})    
            elif len(Ore_lista)==1 :mesaje_specifice.append({"Message":f"La ora {ore}{lista_mesaje}","MessageType":type_of_message})
            else :mesaje_specifice.append({"Message":f"La orele {(ore)}{lista_mesaje}","MessageType":type_of_message})
        type_of_message=type_of_message+1
    mesaj_general='Evita consumul in orele in care panourile solare nu functioneaza,respectiv noaptea.'  
    conn.close()

    return jsonify({'day':day,
                    'Dictionary for Recommendation_types':Recommendation_list,
                    'general_message':mesaj_general,
                    'specific_message':mesaje_specifice,
                    'Hourly_data':[{
                        'hour': Recommendations[i]['hour'],
                        'Recommendation_type': Recommendations[i]['Recommendation_type'],
                        'Hourly_Consumption': consumption_each_hour_result[i][0],
                        'Hourly_Production': total_hourly_production[i],
                        'EpochTime':start_time[0]+(day-1)*24*3600+each_hour_total_radiation_result[i][1]*3600,
                        'Real_Time':time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time[0]+(day-1)*24*3600+each_hour_total_radiation_result[i][1]*3600))
                    }for i in range(24)]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)