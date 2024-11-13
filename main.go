package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"

	"github.com/o-richard/timetablegenerator/timetable"
)

type applicationError struct {
	Key    string   `json:"key"`
	Issues []string `json:"issues"`
}

const (
	swagger = `
	<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="UTF-8"/>
			<link rel="stylesheet" href="/css/swagger-ui.css"/>
			<title>Timetable Generator - Swagger Documentation</title>
			<style>
                *,*:before, *:after { box-sizing: inherit;}
                body {margin: 0; background: #fafafa;}
                html {box-sizing: border-box; overflow: -moz-scrollbars-vertical;overflow-y: scroll;}
			</style>
		</head>
		<body>
			<div id="swagger-ui"></div>
			<script src="/js/swagger-ui-bundle.js"></script>
			<script src="/js/swagger-ui-standalone-preset.js"></script>
			<script> 
                window.onload = function() {    
                    window.ui = SwaggerUIBundle({
                        url: "/openapi/openapi.yaml",
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout",
                        tryItOutEnabled: true,
                        supportedSubmitMethods: ["get", "put", "post", "delete"]
                    });
                };
            </script>
		</body>
	</html>`
	redoc = `
	<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="UTF-8"/>
			<link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet"/>
			<title>Timetable Generator - Redoc Documentation</title>
			<style>body {margin: 0;padding: 0;}</style>
		</head>
		<body><redoc spec-url="/openapi/openapi.yaml"></redoc><script src="/js/redoc-standalone.js"></script></body>
    </html>`
)

func main() {
	var port uint
	flag.UintVar(&port, "port", 1323, "The port used by the http server. Default - 1323.")
	flag.Parse()

	cancel, err := timetable.NewBrowser()
	if err != nil {
		log.Fatal(err)
	}
	defer cancel()

	e := echo.New()
	e.Pre(middleware.AddTrailingSlash())
	e.Use(middleware.Gzip())
	e.Use(middleware.Recover())
	e.Use(middleware.Secure())
	e.Use(middleware.BodyLimitWithConfig(middleware.BodyLimitConfig{Limit: "1M"}))
	e.Static("/", "static")

	e.GET("/", func(c echo.Context) error {
		return c.Redirect(http.StatusFound, "/docs/redoc")
	})
	e.GET("/docs/swagger/", func(c echo.Context) error {
		return c.HTML(http.StatusOK, swagger)
	})
	e.GET("/docs/redoc/", func(c echo.Context) error {
		return c.HTML(http.StatusOK, redoc)
	})
	e.GET("/api/healthz/", func(c echo.Context) error {
		return c.NoContent(http.StatusOK)
	})
	e.POST("/api/generate/", func(c echo.Context) error {
		if !strings.HasPrefix(c.Request().Header.Get(echo.HeaderContentType), echo.MIMEApplicationJSON) {
			return c.NoContent(http.StatusUnsupportedMediaType)
		}

		payload := new(timetable.VSchool)
		if err := (&echo.DefaultBinder{}).BindBody(c, payload); err != nil {
			return c.NoContent(http.StatusUnprocessableEntity)
		}
		school, ok := payload.Validate()
		if !ok {
			return c.NoContent(http.StatusUnprocessableEntity)
		}

		classIssues := school.CheckValidityOfClasses()
		if len(classIssues) != 0 {
			return c.JSON(http.StatusBadRequest, applicationError{Key: "class_validity", Issues: classIssues})
		}
		specificsIssues := school.CheckValidityOfSpecifics()
		if len(specificsIssues) != 0 {
			return c.JSON(http.StatusBadRequest, applicationError{Key: "specifics_validity", Issues: classIssues})
		}
		if !school.GenerateTimetable() {
			return c.JSON(http.StatusBadRequest, applicationError{Key: "timetable_generation"})
		}
		zipFile, zipFileName, err := school.PrintTimetable()
		if err != nil {
			c.Logger().Errorf("unable to print timetable, %v", err)
			return c.NoContent(http.StatusInternalServerError)
		}

		http.ServeContent(c.Response().Writer, c.Request(), zipFileName, time.Now(), zipFile)
		_ = zipFile.Close()
		_ = os.Remove(zipFile.Name())
		return nil
	})

	if err := e.Start(fmt.Sprintf(":%d", port)); err != nil && !errors.Is(err, http.ErrServerClosed) {
		fmt.Println("unable to start server, ", err)
	}
	if err := e.Shutdown(context.Background()); err != nil {
		fmt.Println("unable to shutdown server, ", err)
	}
}
