# App-launcher

This is a configurable applications launcher for Pepper. 

## Pages
You can organise the apps in pages and dispose them as you wish on the home page. 

This is configured using preferences:
* Domain : tool.applauncher.page
* key : page1(2,3,4...)
* Values :

{
    'title': {
        'English':'Name of my page',
        'French':'Nom de ma page',
        ...
    },
    'apps': [
        'app-uuid-1',
        'app-uuid-2',
        ...
    ]
}

Example of values :
    {'title':{'English':'Retail','French':'Vente'},'apps':['product-information','shop-orientation','loyalty-program','satisfaction-survey']}

    {'title':{'English':'Tourism','French':'Tourisme'},'apps':['check-in-7b9a99','check-in-7b9a99', 'loyalty-program', 'satisfaction-survey']}

    {'title':{'English':'Office','French':'Bureau'},'apps':['bank-welcome','bank-welcome', 'loyalty-program', 'satisfaction-survey']}


## Configuration

Domain: tool.applauncher:

* Key: logo / Value : pepper.png
* Key: behaviorNameDisplayed / Value : 1 to show apps names, or 0 to hide them.
* Key : dialogAlwaysRunning / Value : boolean default False : bypass run_dialog and run the dialog automatically.
* Key : hideSystemApps / Value : 1 to filter system apps so they are not displayed in the app list
* Key : hideChoregrapheTestApp / Value : 1 to filter the Choregraphe ".lastUploadedChoregrapheBehavior" so it is no displayed in the app list

Domain
com.aldebaran.system.tablet

* Key : MainActivity / Value : image.png
* Key : MainResourceURL / Value : http://198.18.0.1/apps/app-launcher/resources/background.jpg

Default file of preferences : "defaultPreferences.json"
Located in : html/resources

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


### How to get the icon of an app ?

	1) Using SSH

import qi
s = qi.Session()
s.connect("tcp://127.0.0.1:9559")
pm = s.service("PackageManager")
i = pm.packageIcon("bank-welcome")
import base64
imgEnString = base64.encodestring(i)

unefois l'image png base64 convertie en string, pour l'afficher en html
<img src="data:image/png;base64,'+imgEnString+'"/>


	2) Using python et JS

 python:

	import base64

	def package_icon(self, uuid):
        """Get the icon of a package.
        :param uuid: (str) uuid of the package

        :return: (str) a base64-encoded package icon.
        """
        return base64.encodestring(self.pacman.packageIcon(uuid))

 JS:

 	//id_div, (str) id of the div where you want to add the icon
 	//uuid, (str) application id of the app from which you want to get the icon

 	function get_icon_app(id_div, uuid){
    session.service("DemoLauncher").then( function(dm) { // Replace "DemoLauncher" by the name of your service
        dm.package_icon(uuid).then(function (iconApp){
            $("#"+id_div).append('<div><img src="data:image/png;base64,'+iconApp+'" height=150px width=150px style="margin-bottom:20px"/></div>');
        });
    });
}

## License

This project is licensed under the BSD 3-Clause "New" or "Revised" License - see the [COPYING](COPYING.md) file for details.
