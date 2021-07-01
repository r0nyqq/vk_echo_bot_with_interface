from .initDB import Favorites


class DatabaseUpdater:
    
    def __init__(self, user_id, ticket=None, date=None, orig=None, destination=None):
        """
        Класс отвечающий за апдейт и вытаскивание информации  из базы данных
        :param user_id: id юзера который обращается к бд
        :param ticket: информация о билете
        :param date: дата поездки
        :param orig: название аэропорта отправления
        :param destination: название аэропорта прибытия
        """
        self.cur_user = user_id
        self.ticket = ticket
        self.date = date
        self.orig = orig
        self.destination = destination
    
    def update_db(self):
        check = Favorites.select().where(
            (Favorites.user_id == self.cur_user) & (Favorites.date == self.date) & (Favorites.orig == self.cur_user)
            & (Favorites.destination == self.date)
        )
        if check.exists():
            Favorites.update(
                {
                    Favorites.ticket: self.ticket
                }
            ).where(
                (Favorites.user_id == self.cur_user) & (Favorites.date == self.date) & (Favorites.orig == self.cur_user)
                & (Favorites.destination == self.date))
        else:
            Favorites.create(
                user_id=self.cur_user,
                ticket=self.ticket,
                date=self.date,
                orig=self.orig,
                destination=self.destination
            )
    
    def retrieval_data(self):
        """
        Метод отвечающий за выборку информации из базы данных, если она в нем есть
        :return: выбранные из БД данны за необходимый день
        """
        check = Favorites.select().where(Favorites.user_id == self.cur_user)
        if check.exists():
            return check
