##################################################################################
#File: generate_graph.py
#Author: Onur Ozuduru
#   e-mail: onur.ozuduru { at } gmail.com
#   github: github.com/onurozuduru
#   twitter: twitter.com/OnurOzuduru
#
#License: The MIT License (MIT)
#
#   Copyright (c) 2016 Onur Ozuduru
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#  
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#  
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#
#NOTE: Instagram API has its own license and platform policy,
#   for more information about it please visit:
#   https://www.instagram.com/developer/.
##################################################################################

from instagram.client import InstagramAPI
from pattern.graph import Graph
import lxml.html as L

access_token = "YOUR ACCESS TOKEN" ## Replace with token.
client_secret = "YOUR CLIENT SECRET" ## Replace with secret.

# Name/Path of the folder that keeps output files.
output_path = "MyGraph"
# Class name of the user nodes in the graph. It can be seen on HTML output.
css_user = "node-user"
# Class name of the image nodes in the graph. It can be seen on HTML output.
css_image = "node-photo"

# Distance of the graph.
distance = 20
# Force constant of the graph.
k = 3.0
# Force radius of the graph.
repulsion = 15
# Size of the canvas that includes graph.
width = 1200
height = 600
# JavaScript code that converts URLs of the images nodes to <img> tags in other words
#    it replaces addresses with real images.
js = """
    <script type="text/javascript">
	    window.onload = function() {
            nodeList = document.getElementsByClassName("%(image)s");
	        for(var i = 0; i < nodeList.length; i++) {
	            var url = (nodeList[i].innerText || nodeList[i].textContent);
	            nodeList[i].innerHTML = '<img src="'+url+'" width="75px" height="75px" style="position:absolute; left:-37px; top:-37px; z-index:-1;" />';
            }
            userList = document.getElementsByClassName("%(user)s");
	        for(var i = 0; i < userList.length; i++) {
	            var username = userList[i].innerHTML;
	            userList[i].innerHTML = '<img src="https://openclipart.org/image/36px/svg_to_png/145537/Simple-Red-Heart.png" style="position:absolute; left:-18px; top:-18px; z-index:-1;" />' + username;
            }
            images = document.getElementsByTagName('img');
            for(var i = 0; i < images.length; i++) {
	            images[i].ondragstart = function() { return false; };
            }
    };
    </script>
""" % {"image": css_image, "user": css_user}

# Create new Instagram API.
api = InstagramAPI(access_token=access_token, client_secret=client_secret)
# Create new Graph.
graph = Graph(distance=distance)

# It is for finding user-id of an user.
# It takes only one username (string) as an argument and 
#    returns an User object and its user-id (as string.)
# !! Exact username must be given as argument otherwise that function will return wrong user!
def find_user(username):
    if not username:
        print "Name is empty!"
        return None, None
    res = api.user_search(q="@"+username, count=1)
    if not res:
        print "{user} cannot be found!".format(user=username)
        return None, None
    ret_user = res[0]
    return ret_user, ret_user.id

# It is for getting only the necessary parts of Image objects (which are URLs
#    and name of the users who liked the image.)
# It takes user-id (string) and counter number (integer) that implies number of images to process and
#    returns a list that includes dictionaries in following format:
# {"url": URLofIMAGE, "liked_usernames":[ListofUsernames]}
def recent_media_likes(userid, count):
    if not userid or not count:
        return []
    media_list, _ = api.user_recent_media(user_id=userid, count=count)
    ret = []
    for media in media_list:
        media_dict = {"url":"", "liked_usernames":[]}
        media_dict["url"] = media.images["thumbnail"].url.split('?')[0]
        media_dict["liked_usernames"] = [u.username for u in api.media_likes(media.id)]
        ret.append(media_dict)
    return ret

# It is for creating new nodes and edges between them.
# Example path: [User (who owns images)] -> [Image0] -> [User (who likes Image0)]
#   where brackets([]) shows Nodes and Arrows(->) shows Edges.
def create_nodes(username, media_list):
    css = {username: "owner"}
    graph.add_node(username, fill=(0,0,0,1))
    for media in media_list:
        image = media["url"]
        likes = media["liked_usernames"]
        graph.add_node(image)
        graph.add_edge(username, image, weight=0.0, type='shared-it')
        css[image] = css_image
        for liked_by in likes:
            graph.add_node(liked_by)
            graph.add_edge(image, liked_by, weight=0.0, type='is-liked-by')
            css[liked_by] = css_user
    return graph, css

# It exports the graph to visualize and modifies the HTML code for a nice visualization.   
def create_output(css):
    graph.export(path=output_path, directed=False, width=width, height=height, css=css, k=k, repulsion=repulsion)
    with open(output_path+"/index.html", "r") as f:
        html_data = f.read()
    page = L.fromstring(html_data)
    page.body.insert(page.body.index(page.body.find(".//div[@id='graph']"))+1, L.fragment_fromstring(js))
    with open(output_path+"/index.html", "w") as f:
        f.write(L.tostring(page))

def sort_users_by_likes():
    nodes = graph.nodes
    nodes = filter(lambda n: False if n.id[0:7] == "http://" or n.id[0:8] == "https://" else True, nodes)
    for node in sorted(nodes, key=lambda n: n.weight, reverse=True):
        print '%.2f' % node.weight, node.id
 
def run(username, userid, count):
    _, css = create_nodes(username, recent_media_likes(userid, count))
    create_output(css)
    sort_users_by_likes()
    
if __name__ == "__main__":
# Uncomment below line to create a graph for a different user than yourself.
#    user, userid = find_user("nasa")
    username = "Me" # user.username
    userid = "self" # Comment this line if you are creating a graph for a different user than yourself.
    count = 3
    run(username, userid, count)
