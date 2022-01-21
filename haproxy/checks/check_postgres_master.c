#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>
#include <libpq-fe.h>


// Constants
#define host_regex "^([0-9A-Za-z\\.\\-\\_]+)$"
#define port_regex "^([0-9]+)$"
#define dbName "postgres"
#define pguser "haproxy"
#define expected "f"



int main( int argc, char *argv[] ) {
  char     *pghost,*pgport, *t_port, *t_host, *result;
  regex_t  regex;
  int      ret, rec_count, value;
  PGconn   *conn;
  PGresult *res;
  char conninfo[200];


  /* Haproxy sets the HAPROXY_SERVER_NAME. Lets confirm it is set */
  if( NULL == getenv("HAPROXY_SERVER_NAME") ) {
    printf("HAPROXY_SERVER_NAME is not set\n");
    exit(1);
  }

  /* Haproxy also sets a number of args. We are only interested in 
  the 4th item which contains the port number */

  if ( argc < 5 ) {
    printf("Not enough arguments given\n");
    exit(1);
  }


  t_port = argv[4];
  t_host = getenv("HAPROXY_SERVER_NAME");

  printf("Port provided was %s\n", t_port);
  printf("Host provided was %s\n", t_host);

  /* Check data provided as port */
  ret = regcomp(&regex, port_regex, REG_EXTENDED);
  if (ret) {
    fprintf(stderr, "Could not compile port regex using %s\n", port_regex);
    exit(1);
  } 
 
  ret = regexec(&regex, t_port , 0, NULL, 0);
  if (ret) {
    printf("No Match for port. It does not appear to be a number using %s\n", port_regex);
    exit(1);
  }

    /* Check data provided as host */
  ret = regcomp(&regex, host_regex, REG_EXTENDED);
  if (ret) {
    fprintf(stderr, "Could not compile host regex using %s\n", host_regex );
    exit(1);
  }

  ret = regexec(&regex, t_host , 0, NULL, 0);
  if (ret) {
    printf("No Match for host which failed regex check using %s\n", host_regex);
    exit(1);
  }


  pghost = t_host;
  pgport = t_port;
  regfree(&regex);


  printf("Host Set as %s\n",pghost); 
  printf("Port Set as %s\n",pgport);

  snprintf( conninfo, 200, "dbname=%s port=%s host='%s' sslmode=allow user=%s ", dbName, pgport, pghost, pguser );

  printf("String used is: %s \n", conninfo );


  /* make a connection to the database */
  conn = PQconnectdb( conninfo );

  if (PQstatus(conn) == CONNECTION_BAD) {
    fprintf(stderr, "Connection to database '%s' failed.\n", dbName);
    fprintf(stderr, "%s", PQerrorMessage(conn));
    PQfinish(conn);
    exit(1); 
  }

  /* And run the query to check if we are in recover ( ie: not the master ) */
  res = PQexec(conn, "SELECT pg_is_in_recovery() LIMIT 1;");

  if (PQresultStatus(res) != PGRES_TUPLES_OK) {
    printf("We did not get any data!");
    exit(1);
  }


  rec_count = PQntuples(res);
  if ( rec_count != 1 ) {
    printf("Query should only return 1 record. The query returned %d records", rec_count);
    exit(1);
  }


  result = PQgetvalue(res, 0, 0) ;
  printf( "%s\n", result );
  PQclear(res);

  value = strcmp( result, expected);
  if ( value == 0 ) {
    printf(" Host %s is a master\n", pghost);
  } else {
    printf(" Host %s is not a master\n", pghost);
    exit(1);
  }
  

  return 0;
}
