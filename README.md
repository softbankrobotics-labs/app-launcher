app-launcher

Gestions des préférences

Domaine
tool.applauncher.page

key
page+i

format value
    {'title':{'English':'Retail','French':'Vente'},'apps':['product-information','shop-orientation','loyalty-program','satisfaction-survey']}

    {'title':{'English':'Tourism','French':'Tourisme'},'apps':['check-in-7b9a99','check-in-7b9a99', 'loyalty-program', 'satisfaction-survey']}

    {'title':{'English':'Office','French':'Bureau'},'apps':['bank-welcome','bank-welcome', 'loyalty-program', 'satisfaction-survey']}


Domaine
tool.applauncher

key
logo

format value
pepper.png


Domaine
tool.applauncher

key
behaviorNameDisplayed

format value
    0 (le nom des apps est caché)
    1 (le nom des apps est visible)

Domaine
tool.applauncher

key
dialogAlwaysRunning

format value
    0 (le dialog ne démarre pas automatiquement)
    1 (le dialog démarre automatiquement à la sortie d'app et au boot du robot)

Domaine
com.aldebaran.system.tablet

key
MainActivity

format value
image

Domaine
com.aldebaran.system.tablet

key
MainResourceURL

format value
http://198.18.0.1/apps/app-launcher/resources/background.jpg

Fichier par défaut des préférences "defaultPreferences.json"
Présent dans html/resources

[
    {
        "title":{
            "English":"Retail",
            "French":"Retail"
        },"apps":[
            "product-information","shop-orientation","loyalty-program","satisfaction-survey"]
    },
    {
        "title":{
            "English":"Games",
            "French":"Jeux"
        },"apps":
            ["pepper-play","musicboxes","pepperdetective","seeandlisten","strike_the_pose"]
    },
    {
        "title":{
            "English":"Office",
            "French":"Bureau"
        },"apps":[
        "bank-welcome","loyalty-program","satisfaction-survey"]
    },
    {
        "title":{
            "English":"Pepper",
            "French":"Pepper"
        },"apps":[
        "pepper-presentation","languages-demonstration","mood-mirror","locomotion-dialog"]
    }
]

Récupération de l'icone de l'app

	1) Connexion ssh puis

import qi
s = qi.Session()
s.connect("tcp://127.0.0.1:9559")
pm = s.service("PackageManager")
i = pm.packageIcon("bank-welcome")
import base64
imgEnString = base64.encodestring(i)

unefois l'image png base64 convertie en string, pour l'afficher en html
<img src="data:image/png;base64,'+imgEnString+'"/>


	2) Fonction python et JS

 côté python:

	import base64

	def package_icon(self, uuid):
        """Get the icon of a package.
        :param uuid: (str) uuid of the package

        :return: (str) a base64-encoded package icon.
        """
        return base64.encodestring(self.pacman.packageIcon(uuid))

 côté JS:

 	//id_div, (str) id de la div ou l'on souhaite ajouter l'image
 	//uuid, (str) application id de l'app dont on veut l'image

 	function get_icon_app(id_div, uuid){
    session.service("DemoLauncher").then( function(dm) { //remplacer DemoLauncher par le service dans lequel est ajoutée la fonction python
        dm.package_icon(uuid).then(function (iconApp){
            $("#"+id_div).append('<div><img src="data:image/png;base64,'+iconApp+'" height=150px width=150px style="margin-bottom:20px"/></div>');
        });
    });
}



