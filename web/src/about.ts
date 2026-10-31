// The about page: its picture is the painting from art/, which lives outside web/.
import painting from '../../art/golden-pyramid-with-tunnel-celebration/golden-pyramid-with-tunnel-celebration.jpg?url';

(document.getElementById('painting') as HTMLImageElement).src = painting;
