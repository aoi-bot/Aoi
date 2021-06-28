"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from flask import Flask, request
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session


def setup(app: Flask, connection: Connection, session: Session):
    @app.get('/self-roles/<int:guild_id>')
    def get_self_assignable_roles(guild_id):
        res = connection.execute("select role from selfrole where guild=?", (guild_id,))
        res = [r["role"] for r in res.fetchall()]
        return {
            "results": res
        }

    @app.put('/self-roles/<int:guild_id>')
    def add_self_assignable_role(guild_id):
        role_id = request.json["role"]
        roles = get_self_assignable_roles(guild_id)["results"]
        if role_id in roles:
            return {"results": False}
        session.execute("insert into selfrole (guild, role) values (:guild,:role)",
                        {
                            "guild": guild_id,
                            "role": role_id
                        })
        session.commit()
        return {"results": True}

    @app.delete('/self-roles/<int:guild_id>')
    def delete_self_assignable_role(guild_id):
        role_id = request.json["role"]
        roles = get_self_assignable_roles(guild_id)["results"]
        if role_id not in roles:
            return {"results": False}
        session.execute("delete from selfrole where guild=:guild and role=:role",
                        {
                            "guild": guild_id,
                            "role": role_id
                        })
        session.commit()
        return {"results": True}
