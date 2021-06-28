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
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from database_api.core import SelfRole


def setup(app: Flask, engine: Engine, session: Session):
    @app.get('/self-roles/<int:guild_id>')
    def get_self_assignable_roles(guild_id):
        roles = [res.role for res in session.query(SelfRole).where(SelfRole.guild == guild_id).all()]
        return {
            "results": roles
        }

    @app.put('/self-roles/<int:guild_id>')
    def add_self_assignable_role(guild_id):
        role_id = request.json["role"]
        roles = [res.role for res in session.query(SelfRole).where(SelfRole.guild == guild_id).all()]
        if role_id in roles:
            return {"results": False}
        session.add(SelfRole(guild=guild_id, role=role_id))
        session.commit()
        return {"results": True}

    @app.delete('/self-roles/<int:guild_id>')
    def delete_self_assignable_role(guild_id):
        role_id = request.json["role"]
        roles = [res.role for res in session.query(SelfRole).where(SelfRole.guild == guild_id).all()]
        if role_id not in roles:
            return {"results": False}
        inst = session.query(SelfRole).filter_by(guild=guild_id, role=role_id).one()
        session.delete(inst)
        session.commit()
        return {"results": True}
