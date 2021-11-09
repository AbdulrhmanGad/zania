# -*- coding: utf-8 -*-

import werkzeug

from odoo import http
from odoo.http import Response, request


class RingdeskAuth(http.Controller):
    @http.route(['/ringdesk/login'], type='http', auth="user", website=True)
    def login_popup(self):
        return Response( """
        <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="X-UA-Compatible" content="ie=edge">
                <title>Document</title>
            </head>
            <body>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/oidc-client/1.8.2/oidc-client.min.js"> </script>
                <script>
                    new Oidc.UserManager({ response_mode: "query" }).signinPopupCallback().then(function () {
                        window.close();
                    }).catch(function (e) {
                        window.close();
                        console.error(e);
                    });    
                </script>
            </body>
            </html>""", status=200)
    
    @http.route(['/ringdesk/logout'], type="http", auth="user", website=True)
    def logout_popup(self):
        return Response("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="X-UA-Compatible" content="ie=edge">
            <title>Document</title>
        </head>
        <body>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/oidc-client/1.8.2/oidc-client.min.js"> </script>
            <script>
                new Oidc.UserManager({ response_mode: "query" }).signoutPopupCallback().then(function () {
                    window.close();
                }).catch(function (e) {
                    window.close();
                    console.error(e);
                });          
            </script>
        </body>
        </html>
        """, status=200)
