from sqlalchemy import event, create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv
import datetime
import oracledb
import os

load_dotenv()

class Config:
    # Carrega as configurações dos bancos
    _ORACLE = {
        "INSTANT_CLIENT":   os.getenv("INSTANT_CLIENT"),
        "TSN":              os.getenv("TSN"),
        "DB_USER":          os.getenv("DB_USER"),
        "DB_PASS":          os.getenv("DB_PASS")
    }
    ARRAYSIZE = 15000

    _APPLICATION = {
        "APP_SECRET": os.getenv("SECRET", "PutTheKeyBro"),
        "SRV_HOST": os.getenv("SRV_HOST", "localhost:8020")
    }

    # ============================================================================
    # ================================= INIT =====================================
    # ============================================================================

    def __init__(self) -> None:
        self._oracle_engine = self._get_oracle_engine()

    # ============================================================================
    # ============================= APLICATION ===================================
    # ============================================================================
    
    def get_aplication_key(self) -> str:
        return self._APPLICATION['APP_SECRET']

    def get_aplication_host(self) -> str:
        return self._APPLICATION['SRV_HOST']

    # ============================================================================
    # ============================== ORACLEDB ====================================
    # ============================================================================

    def get_oracle_session(self):
        """Retorna um SessionMaker para o OracleDB."""
        return sessionmaker(bind=self._oracle_engine)

    def _get_oracle_engine(self):
        """
        Inicializa o Oracle client, cria e retorna um engine SQLAlchemy
        para o OracleDB usando TNS name configurado.
        """
        # 1) Inicializa o Oracle Instant Client
        try:
            oracledb.init_oracle_client(lib_dir=self._ORACLE['INSTANT_CLIENT'])
        except Exception as e:
            print(f"Erro ao inicializar Oracle client: {e}")
            exit(1)

        # 2) Recupera TSN (TNS name) definido pela empresa
        tsn = self._ORACLE['TSN']

        # 3) Monta a URL do SQLAlchemy: 
        #    note que o dialect é oracle+oracledb e o DSN é o TNS name
        user = self._ORACLE['DB_USER']
        pw   = quote_plus(self._ORACLE['DB_PASS']) # type: ignore
        url  = f"oracle+oracledb://{user}:{pw}@{tsn}"

        # 4) Cria engine e testa conexão
        engine = create_engine(url, arraysize=self.ARRAYSIZE)

        # —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
        # injeta automaticamente o ALTER SESSION toda vez que uma conexão
        @event.listens_for(engine, "connect")
        def _set_nls_date_format(dbapi_connection, connection_record):
            # dbapi_connection é o objeto oracledb.Connection
            cursor = dbapi_connection.cursor()
            cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'DD/MM/YYYY'")
            cursor.close()
        # —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––


        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT SYSDATE FROM DUAL")).fetchone()
                assert result is not None, "Teste DQL retornou nenhuma linha"

                if not isinstance(result[0], datetime.datetime):
                    raise RuntimeError("Retorno inesperado no teste DQL")
                print(f"Conectado com sucesso ao OracleDB (TSN={tsn}): {result[0]}")
            return engine
        except Exception as e:
            print(f"Erro ao conectar ao OracleDB (TSN={tsn}): {e}")
            exit(1)


cfg = Config()

QUERY_TEXT = """SELECT
    H.CD_UNID_IND,
    SG_FILIAL AS DE_UNID_IND,
    H.CD_UPNIVEL1,
    H.CD_UPNIVEL2,
    H.CD_UPNIVEL3,
    H.CD_FREN_TRAN,
    TO_CHAR(H.HR_SAIDA, 'DD/MM/YYYY HH24:MI:SS') HR_SAIDA,
    H.QT_LIQUIDO QT_CANA,
    H.QT_BRIX QT_BRIX,
    H.QT_PEX QT_POL,
    H.QT_FIBRA QT_FIBRA,
    H.QT_IMPUR_TERRA,
    H.QT_IMPUR_VEG,
    H.QT_DISTANCIA
FROM
    PIMSCS.APT_CARGAS H
    LEFT JOIN (
      SELECT
          B.CD_FIL_BI,
          B.SG_FILIAL
      FROM
          PRD.USFILIAL B
      WHERE B.CD_FIL IN (1,2,13,34,15,16,4,19,72,3,18)
    ) ON CD_FIL_BI = H.CD_UNID_IND
WHERE
    H.DT_SAIDA BETWEEN TRUNC(SYSDATE-2) AND SYSDATE"""


if __name__ == '__main__':
    # Pequeno teste
    #engine = cfg.get_oracle_session()
    pass