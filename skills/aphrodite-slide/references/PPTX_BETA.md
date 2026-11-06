# Editable PPTX Exporter · Beta

```bash
pip install python-pptx
python scripts/studio.py pptx examples/logistics/deck.json --out build/logistics.pptx
```

The adapter creates **native editable text, shapes and simple bars** from deck JSON, rather than screenshot slides; it covers common layouts (cover, metrics, columns, process, timeline, comparison, bar chart, quote, summary). It is not a pixel-identical HTML-to-PPTX converter. Complex assets and advanced chart formatting will require refinement. Unsupported HTML animations do not migrate into PPTX. The `image-split` layout currently exports its text/placeholder only; users need to add or review the local image in PowerPoint.

Always inspect the exported PPTX separately and make no blanket promise that all PPTX elements match HTML. For advanced enterprise PPTX workflows, consider integrating an external properly licensed skill after technical and license review; do not automatically vendor third-party source code.
