import peewee

database = peewee.SqliteDatabase('chatbotfavoritesdb.sl3')


class BaseTable(peewee.Model):
    # В подклассе Meta указываем подключение к той или иной базе данных
    class Meta:
        database = database
 
        
class Favorites(BaseTable):
    id = peewee.PrimaryKeyField()
    user_id = peewee.IntegerField()
    ticket = peewee.CharField()
    date = peewee.DateTimeField()
    orig = peewee.CharField()
    destination = peewee.CharField()


database.create_tables([Favorites])