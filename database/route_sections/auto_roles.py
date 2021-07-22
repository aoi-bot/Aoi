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
    @app.get('/auto-roles/<int:guild_id>')
    def get_auto_roles(guild_id):
        res = connection.execute("select roles from autorole where guild=?", (guild_id,))
        res = res.fetchone() or []
        return {
            "results": [int(x) for x in res[0].split(",")] if res else []
        }

    @app.put('/auto-roles/<int:guild_id>')
    def add_auto_role(guild_id):
        role_id = request.json["role"]
        roles = get_auto_roles(guild_id)["results"]
        if role_id in roles:
            return {"results": False}
        if not roles:
            connection.execute("insert into autorole (guild, roles) values (?,?)",
                               (guild_id, str(role_id)))
        else:
            connection.execute("update autorole set roles=? where guild=?",
                               (",".join(map(str, roles + [role_id])), guild_id))
        session.commit()
        return {"results": True}

    @app.delete('/auto-roles/<int:guild_id>')
    def delete_auto_role(guild_id):
        role_id = request.json["role"]
        roles = get_auto_roles(guild_id)["results"]
        if not roles or role_id not in roles:
            return {"results": False}
        roles.remove(role_id)
        if not roles:
            connection.execute("delete from autorole where guild=?",
                               (guild_id, ))
        else:
            connection.execute("update autorole set roles=? where guild=?",
                               (",".join(map(str, roles)), guild_id))
        session.commit()
        return {"results": True}
