package timetable

import (
	"context"
	"fmt"
	"os"
	"sync"

	"github.com/chromedp/cdproto/page"
	"github.com/chromedp/chromedp"
)

var (
	bOnce          sync.Once
	errB           error
	bCtx           context.Context
	bCtxCancelFunc context.CancelFunc
)

// Initializes the browser session used for pdf generation. The caller is responsible for termination.
func NewBrowser() (context.CancelFunc, error) {
	bOnce.Do(func() {
		bCtx, bCtxCancelFunc = chromedp.NewContext(context.Background())
		if err := chromedp.Run(bCtx); err != nil {
			errB = fmt.Errorf("unable to start browser session, %w", err)
		}
	})
	return bCtxCancelFunc, errB
}

func generatePdf(filepath, body string) error {
	if bCtx == nil || bCtx.Err() != nil {
		panic("browser session must be active and ongoing")
	}

	html := fmt.Sprintf(`<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"><style>table,tr,th,td {text-align: center;border: 1px solid black;border-collapse: collapse;}th {padding: 2px;}td {padding-left: 3px;padding-right: 3px;}</style></head><body style="background-color: white; display: flex;justify-content: center; flex-direction: column;">%v</body></html>`, body)
	ctx, cancel := chromedp.NewContext(bCtx)
	defer cancel()

	err := chromedp.Run(ctx,
		chromedp.Navigate("about:blank"),
		chromedp.ActionFunc(func(ctx context.Context) error {
			loadCtx, cancel := context.WithCancel(ctx)
			defer cancel()

			var wg sync.WaitGroup
			wg.Add(1)
			chromedp.ListenTarget(loadCtx, func(ev interface{}) {
				if _, ok := ev.(*page.EventLoadEventFired); ok {
					cancel()
					wg.Done()
				}
			})

			frameTree, err := page.GetFrameTree().Do(ctx)
			if err != nil {
				return fmt.Errorf("unable to obtain frame tree, %w", err)
			}
			if err := page.SetDocumentContent(frameTree.Frame.ID, html).Do(ctx); err != nil {
				return fmt.Errorf("unable to set document content, %w", err)
			}

			wg.Wait()
			return nil
		}),
		chromedp.ActionFunc(func(ctx context.Context) error {
			buf, _, err := page.PrintToPDF().WithLandscape(true).WithPrintBackground(true).WithPaperHeight(14).Do(ctx)
			if err != nil {
				return fmt.Errorf("unable to print to pdf, %w", err)
			}
			if err := os.WriteFile(filepath, buf, 0o600); err != nil {
				return fmt.Errorf("unable to write to file, %w", err)
			}
			return nil
		}),
	)
	return err
}
